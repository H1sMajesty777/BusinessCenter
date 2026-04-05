# backend/api/ml_models/predictor.py
"""
Главный класс-фасад для ML предсказаний
"""
import pandas as pd
import numpy as np
import joblib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import hashlib

from .config import config
from .feature_extractor import feature_extractor
from .training.synthetic import data_generator, target_generator
from .monitoring.metrics import ModelMonitor
from .models.ensemble import EnsembleModel

logger = logging.getLogger(__name__)


class ProductionRentalPredictor:
    """
    Production-ready предиктор аренды офисов
    
    Features:
    - Автоматическое сохранение/загрузка модели
    - Кэширование предсказаний
    - Мониторинг качества
    - Детектирование дрейфа данных
    - Graceful degradation
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.is_trained = False
        self.metadata = {}
        
        # Компоненты
        self.monitor = ModelMonitor()
        
        # Кэш предсказаний
        self._prediction_cache = {}
        
        # Загружаем существующую модель
        self._load_model()
    
    def _load_model(self):
        """Загрузка сохранённой модели"""
        try:
            if config.model_weights_path.exists():
                self.model = joblib.load(config.model_weights_path)
                self.scaler = joblib.load(config.scaler_path)
                
                if config.model_metadata_path.exists():
                    with open(config.model_metadata_path, 'r') as f:
                        self.metadata = json.load(f)
                
                self.feature_names = self.metadata.get('feature_names', [])
                self.is_trained = True
                
                logger.info(f"   Model loaded. Version: {self.metadata.get('version', 'unknown')}")
                logger.info(f"   Trained at: {self.metadata.get('trained_at', 'unknown')}")
                logger.info(f"   Samples: {self.metadata.get('samples_count', 0)}")
                logger.info(f"   AUC: {self.metadata.get('metrics', {}).get('roc_auc', 0):.3f}")
            else:
                logger.info("No existing model found. Model needs training.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.is_trained = False
    
    def _save_model(self):
        """Сохранение модели с метаданными"""
        try:
            # Сохраняем веса
            joblib.dump(self.model, config.model_weights_path)
            joblib.dump(self.scaler, config.scaler_path)
            
            # Сохраняем метаданные
            with open(config.model_metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
            
            # ИСПРАВЛЕНО: используем MODEL_DIR вместо model_dir
            logger.info(f"Model saved to {config.MODEL_DIR}")
            
            # Сохраняем бэкап
            backup_path = config.MODEL_DIR / f"backup_{self.metadata['version']}.pkl"
            joblib.dump(self.model, backup_path)
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise
    
    def train(self, conn, force_retrain: bool = False) -> Dict[str, Any]:
        """
        Обучение модели
        """
        if self.is_trained and not force_retrain:
            return {
                "status": "skipped",
                "message": "Model already trained. Use force_retrain=True to retrain.",
                "metadata": self.metadata
            }
        
        logger.info("=" * 60)
        logger.info("STARTING MODEL TRAINING")
        logger.info("=" * 60)
        
        try:
            # 1. Извлекаем признаки
            logger.info("Step 1: Extracting features...")
            df = feature_extractor.extract_features(conn)
            
            if len(df) < 10:
                raise ValueError(f"Insufficient data: only {len(df)} samples")
            
            # 2. Создаём целевую переменную
            logger.info("Step 2: Creating target variable...")
            cursor = conn.cursor()
            target = []
            for office_id in df['office_id']:
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM contracts 
                    WHERE office_id = %s 
                    AND signed_at > NOW() - INTERVAL '3 months'
                """, (int(office_id),))
                row = cursor.fetchone()
                count = row['cnt'] if row else 0
                target.append(1 if count > 0 else 0)
            cursor.close()
            
            df['target'] = target
            self.feature_names = [c for c in df.columns if c not in ['office_id', 'target', 'office_number']]
            
            # 3. Проверяем дисбаланс
            pos_ratio = df['target'].mean()
            logger.info(f"Positive class ratio: {pos_ratio:.3f}")
            
            # 4. Генерируем синтетические данные при необходимости
            n_synthetic = 0
            if pos_ratio < 0.1 or pos_ratio > 0.9:
                logger.info("Step 3: Generating synthetic data (class imbalance detected)...")
                
                X_real = df[self.feature_names].values
                y_real = df['target'].values
                
                # Обучаем генераторы
                data_generator.fit(X_real, self.feature_names)
                target_generator.fit(X_real, y_real)
                
                # Генерируем данные
                n_synthetic = max(len(df) * 2, 500)
                X_synthetic = data_generator.generate(n_synthetic).values
                y_synthetic = target_generator.generate(X_synthetic)
                
                # Добавляем к реальным данным
                df_synthetic = pd.DataFrame(X_synthetic, columns=self.feature_names)
                df_synthetic['target'] = y_synthetic
                
                df = pd.concat([df, df_synthetic], ignore_index=True)
                logger.info(f"Dataset size after augmentation: {len(df)} samples")
            
            # 5. Подготовка данных для обучения
            logger.info("Step 4: Preparing data for training...")
            X = df[self.feature_names].values
            y = df['target'].values
            
            # 6. Обучение модели
            logger.info("Step 5: Training ensemble model...")
            ensemble = EnsembleModel(random_state=42)
            result = ensemble.train(X, y)
            
            self.model = ensemble
            self.scaler = ensemble.scaler
            self.is_trained = True
            
            # 7. Сохраняем метаданные
            self.metadata = {
                "version": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "trained_at": datetime.now().isoformat(),
                "samples_count": len(df),
                "real_samples": len(df) - n_synthetic,
                "synthetic_samples": n_synthetic,
                "feature_names": self.feature_names,
                "feature_count": len(self.feature_names),
                "metrics": result['metrics'],
                "feature_importance": result.get('feature_importance', []),
                "data_hash": hashlib.md5(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()
            }
            
            # 8. Сохраняем модель
            self._save_model()
            
            logger.info("=" * 60)
            logger.info(f"TRAINING COMPLETE!")
            logger.info(f"   AUC: {result['metrics']['roc_auc']:.3f}")
            logger.info(f"   Accuracy: {result['metrics']['accuracy']:.3f}")
            logger.info("=" * 60)
            
            return {
                "status": "success",
                "metadata": self.metadata,
                "metrics": result['metrics'],
                "feature_importance": result.get('feature_importance', [])
            }
            
        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def predict(self, conn, office_id: int, use_cache: bool = True) -> Dict[str, Any]:
        """
        Предсказание для одного офиса
        
        Args:
            conn: PostgreSQL соединение
            office_id: ID офиса
            use_cache: Использовать кэш
        
        Returns:
            Dict с предсказанием
        """
        # Проверяем кэш
        cache_key = f"pred_{office_id}"
        if use_cache and cache_key in self._prediction_cache:
            cached = self._prediction_cache[cache_key]
            if (datetime.now() - cached['timestamp']).seconds < config.CACHE_TTL_SECONDS:
                logger.info(f"Returning cached prediction for office {office_id}")
                return cached['result']
        
        # Если модель не обучена, возвращаем эвристику
        if not self.is_trained:
            return self._heuristic_prediction(conn, office_id)
        
        try:
            # Извлекаем признаки
            df = feature_extractor.extract_features(conn, [office_id])
            
            if len(df) == 0:
                return {"error": f"Office {office_id} not found"}
            
            # Проверяем наличие всех признаков
            missing_features = set(self.feature_names) - set(df.columns)
            if missing_features:
                logger.warning(f"Missing features: {missing_features}")
                # Добавляем недостающие признаки с нулями
                for feat in missing_features:
                    df[feat] = 0
            
            X = df[self.feature_names].values
            
            # Предсказание
            probability = float(self.model.predict_proba(X)[0, 1])
            
            # Определяем категорию
            if probability >= 0.7:
                category = "high"
                description = "Высокая вероятность аренды! Офис востребован."
                recommendation = "Срочно свяжитесь с потенциальными арендаторами"
            elif probability >= 0.4:
                category = "medium"
                description = "Средняя вероятность аренды. Есть потенциал."
                recommendation = "Улучшите презентацию офиса"
            else:
                category = "low"
                description = "Низкая вероятность аренды. Требуется анализ."
                recommendation = "Рассмотрите снижение цены или акции"
            
            result = {
                "office_id": office_id,
                "probability": probability,
                "probability_percent": round(probability * 100, 1),
                "category": category,
                "description": description,
                "recommendation": recommendation,
                "model_version": self.metadata.get('version', 'unknown'),
                "timestamp": datetime.now().isoformat()
            }
            
            # Сохраняем в кэш
            self._prediction_cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now()
            }
            
            # Очищаем старый кэш
            self._clean_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed for office {office_id}: {e}")
            return self._heuristic_prediction(conn, office_id)
    
    def predict_batch(self, conn, office_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Массовое предсказание
        """
        results = []
        for office_id in office_ids:
            result = self.predict(conn, office_id, use_cache=True)
            results.append(result)
        
        # Сортируем по вероятности
        results.sort(key=lambda x: x.get('probability', 0), reverse=True)
        
        return results
    
    def _heuristic_prediction(self, conn, office_id: int) -> Dict[str, Any]:
        """
        Эвристическое предсказание (fallback)
        """
        cursor = conn.cursor()
        
        try:
            # Базовая статистика
            cursor.execute("""
                SELECT 
                    o.price_per_month,
                    o.area_sqm,
                    (SELECT COUNT(*) FROM office_views WHERE office_id = %s) as views,
                    (SELECT COUNT(*) FROM applications WHERE office_id = %s) as apps,
                    (SELECT COUNT(*) FROM contracts WHERE office_id = %s) as contracts
                FROM offices o
                WHERE o.id = %s
            """, (office_id, office_id, office_id, office_id))
            
            row = cursor.fetchone()
            if not row:
                return {"error": f"Office {office_id} not found"}
            
            # Простая эвристика
            score = 0
            if row[2] >= 10: score += 0.3
            if row[3] >= 2: score += 0.3
            if row[4] >= 1: score += 0.2
            if row[0] < 30000: score += 0.2
            
            probability = min(0.95, score)
            
            return {
                "office_id": office_id,
                "probability": probability,
                "probability_percent": round(probability * 100, 1),
                "category": "high" if probability >= 0.7 else "medium" if probability >= 0.4 else "low",
                "description": "Эвристическое предсказание (модель не обучена)",
                "model_version": "heuristic",
                "timestamp": datetime.now().isoformat()
            }
        finally:
            cursor.close()
    
    def _clean_cache(self):
        """Очистка старого кэша"""
        now = datetime.now()
        expired_keys = [
            key for key, value in self._prediction_cache.items()
            if (now - value['timestamp']).seconds > config.CACHE_TTL_SECONDS
        ]
        for key in expired_keys:
            del self._prediction_cache[key]
        
        # Ограничиваем размер кэша
        if len(self._prediction_cache) > config.MAX_CACHE_SIZE:
            # Удаляем самые старые
            sorted_items = sorted(
                self._prediction_cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            for key, _ in sorted_items[:len(self._prediction_cache) - config.MAX_CACHE_SIZE]:
                del self._prediction_cache[key]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Информация о модели"""
        return {
            "is_trained": self.is_trained,
            "metadata": self.metadata if self.is_trained else {},
            "cache_size": len(self._prediction_cache),
            "feature_names": self.feature_names[:10] if self.feature_names else [],
            "feature_count": len(self.feature_names) if self.feature_names else 0
        }


# Глобальный экземпляр для использования в API
production_predictor = ProductionRentalPredictor()