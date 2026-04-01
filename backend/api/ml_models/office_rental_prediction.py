"""
Office Rental Prediction - Real ML implementation
Прогнозирование вероятности аренды офиса на основе:
- просмотров офисов
- заявок на аренду
- истории договоров
- характеристик офиса
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.pipeline import Pipeline
import joblib
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')


class OfficeRentalPredictor:
    """
    ML модель для прогнозирования аренды офисов
    
    Особенности:
    - Использует RandomForestClassifier + GradientBoosting
    - Автоматическое переобучение при добавлении новых данных
    - Выдача важности признаков
    """
    
    def __init__(self, model_path: str = None):
        """
        Инициализация предиктора
        
        Args:
            model_path: Путь для сохранения модели (опционально)
        """
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.is_trained = False
        self.model_path = model_path or os.path.join(
            os.path.dirname(__file__), 
            'rental_model.joblib'
        )
        self.scaler_path = self.model_path.replace('.joblib', '_scaler.joblib')
        
        # Загрузка существующей модели если есть
        self._load_model()
    
    def _load_model(self):
        """Загрузка сохранённой модели"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                print(f"Модель загружена из {self.model_path}")
            else:
                print("ℹСохранённая модель не найдена, будет создана новая")
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
    
    def _save_model(self):
        """Сохранение модели"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            print(f"Модель сохранена в {self.model_path}")
        except Exception as e:
            print(f"Ошибка сохранения модели: {e}")
    
    def _extract_features_from_db(self, conn, office_ids: List[int] = None) -> pd.DataFrame:
        """
        Извлечение признаков из базы данных
        
        Args:
            conn: PostgreSQL соединение
            office_ids: Список ID офисов (если None - все)
        
        Returns:
            DataFrame с признаками и целевой переменной
        """
        cursor = conn.cursor()
        
        # Получаем список офисов
        if office_ids:
            office_ids_str = ','.join(str(i) for i in office_ids)
            offices_query = f"""
                SELECT id, office_number, floor, area_sqm, price_per_month, 
                       description, amenities, is_free, created_at
                FROM offices WHERE id IN ({office_ids_str})
            """
        else:
            offices_query = """
                SELECT id, office_number, floor, area_sqm, price_per_month, 
                       description, amenities, is_free, created_at
                FROM offices
            """
        
        cursor.execute(offices_query)
        offices_data = cursor.fetchall()
        
        features_list = []
        
        for office in offices_data:
            office_id = office['id']
            
            # 1. Статистика просмотров
            cursor.execute("""
                SELECT 
                    COUNT(*) as view_count,
                    COALESCE(AVG(duration_seconds), 0) as avg_duration,
                    COALESCE(SUM(CASE WHEN is_contacted THEN 1 ELSE 0 END), 0) as contact_count,
                    COUNT(DISTINCT user_id) as unique_viewers,
                    COUNT(CASE WHEN viewed_at > NOW() - INTERVAL '30 days' THEN 1 END) as views_last_30d,
                    COUNT(CASE WHEN viewed_at > NOW() - INTERVAL '7 days' THEN 1 END) as views_last_7d
                FROM office_views 
                WHERE office_id = %s
            """, (office_id,))
            views_stats = cursor.fetchone()
            
            # 2. Статистика заявок
            cursor.execute("""
                SELECT 
                    COUNT(*) as application_count,
                    COUNT(CASE WHEN status_id = 2 THEN 1 END) as approved_count,
                    COUNT(CASE WHEN status_id = 3 THEN 1 END) as rejected_count,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 1 END) as apps_last_30d
                FROM applications 
                WHERE office_id = %s
            """, (office_id,))
            app_stats = cursor.fetchone()
            
            # 3. История аренды (договоры)
            cursor.execute("""
                SELECT 
                    COUNT(*) as contract_count,
                    COALESCE(AVG(total_amount), 0) as avg_contract_amount,
                    COUNT(CASE WHEN status_id = 4 THEN 1 END) as active_contracts,
                    COUNT(CASE WHEN end_date > CURRENT_DATE THEN 1 END) as future_contracts
                FROM contracts 
                WHERE office_id = %s
            """, (office_id,))
            contract_stats = cursor.fetchone()
            
            # 4. Характеристики офиса
            floor = office['floor']
            area = office['area_sqm']
            price = office['price_per_month']
            price_per_sqm = price / area if area > 0 else 0
            
            # Конкуренция на этаже
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_on_floor,
                    SUM(CASE WHEN is_free THEN 1 ELSE 0 END) as free_on_floor
                FROM offices 
                WHERE floor = %s
            """, (floor,))
            floor_stats = cursor.fetchone()
            
            competition_ratio = floor_stats['free_on_floor'] / floor_stats['total_on_floor'] if floor_stats['total_on_floor'] > 0 else 1
            
            # 5. Целевая переменная: была ли аренда в последние 3 месяца
            cursor.execute("""
                SELECT COUNT(*) as recent_rental
                FROM contracts 
                WHERE office_id = %s 
                AND signed_at > NOW() - INTERVAL '3 months'
            """, (office_id,))
            recent = cursor.fetchone()
            
            target = 1 if recent['recent_rental'] > 0 else 0
            
            # Собираем признаки
            features = {
                'office_id': office_id,
                'floor': floor,
                'area_sqm': area,
                'price_per_month': price,
                'price_per_sqm': price_per_sqm,
                'competition_ratio': competition_ratio,
                'view_count': views_stats['view_count'] or 0,
                'avg_view_duration': views_stats['avg_duration'] or 0,
                'contact_rate': (views_stats['contact_count'] / views_stats['view_count'] 
                                if views_stats['view_count'] > 0 else 0),
                'unique_viewers': views_stats['unique_viewers'] or 0,
                'views_last_30d': views_stats['views_last_30d'] or 0,
                'views_last_7d': views_stats['views_last_7d'] or 0,
                'application_count': app_stats['application_count'] or 0,
                'approval_rate': (app_stats['approved_count'] / app_stats['application_count'] 
                                 if app_stats['application_count'] > 0 else 0),
                'apps_last_30d': app_stats['apps_last_30d'] or 0,
                'contract_count': contract_stats['contract_count'] or 0,
                'avg_contract_amount': contract_stats['avg_contract_amount'] or 0,
                'has_active_contract': 1 if contract_stats['active_contracts'] > 0 else 0,
                'is_free': 1 if office['is_free'] else 0,
                'target': target
            }
            
            features_list.append(features)
        
        cursor.close()
        
        df = pd.DataFrame(features_list)
        return df
    
    def _generate_synthetic_data(self, n_samples: int = 500) -> pd.DataFrame:
        """
        Генерация синтетических данных для обучения модели
        Используется когда в БД недостаточно реальных данных
        """
        np.random.seed(42)
        
        data = []
        
        for i in range(n_samples):
            # Базовые характеристики офиса
            floor = np.random.choice([1, 2, 3, 4, 5], p=[0.3, 0.25, 0.2, 0.15, 0.1])
            area = np.random.uniform(20, 200)
            price_per_sqm = np.random.uniform(300, 800) * (1 - (floor-1) * 0.03)  # Чем выше этаж, тем дороже
            price = area * price_per_sqm
            
            # Конкуренция на этаже
            competition_ratio = np.random.beta(2, 5)  # В основном мало свободных
            
            # Просмотры
            view_count = np.random.poisson(15) * (1 + 1/price_per_sqm*500)
            view_count = max(0, min(100, int(view_count)))
            
            avg_view_duration = np.random.exponential(60) * (1 + competition_ratio * 2)
            contact_rate = np.random.beta(2, 8) * (1 + avg_view_duration/300)
            contact_rate = min(0.8, contact_rate)
            
            unique_viewers = int(view_count * np.random.uniform(0.3, 0.8))
            views_last_30d = int(view_count * np.random.uniform(0.2, 0.6))
            views_last_7d = int(views_last_30d * np.random.uniform(0.2, 0.5))
            
            # Заявки
            application_count = int(np.random.poisson(view_count * 0.15))
            approval_rate = np.random.beta(5, 3) if application_count > 0 else 0
            apps_last_30d = int(application_count * np.random.uniform(0.3, 0.7))
            
            # Договоры
            contract_count = int(np.random.poisson(application_count * 0.4))
            avg_contract_amount = price * np.random.uniform(0.8, 1.5) if contract_count > 0 else 0
            has_active_contract = np.random.choice([0, 1], p=[0.7, 0.3])
            
            is_free = np.random.choice([0, 1], p=[0.6, 0.4])
            
            # Целевая переменная: вероятность аренды зависит от признаков
            score = (
                view_count * 0.02 +
                application_count * 0.15 +
                contact_rate * 5 +
                (1 - competition_ratio) * 3 +
                (1 if is_free else 0) * 2 +
                (price_per_sqm / 1000) * 1
            )
            probability = 1 / (1 + np.exp(-score/5))  # sigmoid
            target = 1 if np.random.random() < probability else 0
            
            data.append({
                'floor': floor,
                'area_sqm': area,
                'price_per_month': price,
                'price_per_sqm': price_per_sqm,
                'competition_ratio': competition_ratio,
                'view_count': view_count,
                'avg_view_duration': avg_view_duration,
                'contact_rate': contact_rate,
                'unique_viewers': unique_viewers,
                'views_last_30d': views_last_30d,
                'views_last_7d': views_last_7d,
                'application_count': application_count,
                'approval_rate': approval_rate,
                'apps_last_30d': apps_last_30d,
                'contract_count': contract_count,
                'avg_contract_amount': avg_contract_amount,
                'has_active_contract': has_active_contract,
                'is_free': is_free,
                'target': target
            })
        
        df = pd.DataFrame(data)
        
        # Добавляем реалистичные корреляции
        df['view_count'] = df['view_count'].clip(0, 100)
        df['application_count'] = df['application_count'].clip(0, 30)
        
        return df
    
    def train(self, conn, force_retrain: bool = False) -> Dict[str, Any]:
        """
        Обучение модели на данных из БД
        
        Args:
            conn: PostgreSQL соединение
            force_retrain: Принудительное переобучение
        
        Returns:
            Dict с результатами обучения
        """
        print("Начинаем обучение модели...")
        
        try:
            # Пытаемся получить реальные данные из БД
            df_real = self._extract_features_from_db(conn)
            
            if len(df_real) >= 20:  # Достаточно реальных данных
                df = df_real
                print(f"Используем реальные данные: {len(df)} записей")
            else:
                # Используем синтетические данные
                df_synth = self._generate_synthetic_data(500)
                if len(df_real) > 0:
                    df = pd.concat([df_real, df_synth], ignore_index=True)
                    print(f"Используем смешанные данные: {len(df_real)} реальных + {len(df_synth)} синтетических")
                else:
                    df = df_synth
                    print(f"Используем синтетические данные: {len(df)} записей")
            
            # Подготовка признаков
            feature_cols = [col for col in df.columns if col not in ['office_id', 'target']]
            self.feature_columns = feature_cols
            
            X = df[feature_cols].values
            y = df['target'].values
            
            # Нормализация
            X_scaled = self.scaler.fit_transform(X)
            
            # Разделение на train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Ансамбль моделей
            rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                class_weight='balanced'
            )
            
            gb_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            
            # Обучаем обе модели
            rf_model.fit(X_train, y_train)
            gb_model.fit(X_train, y_train)
            
            # Создаём ансамбль (усреднение вероятностей)
            class EnsembleModel:
                def __init__(self, rf, gb):
                    self.rf = rf
                    self.gb = gb
                
                def predict_proba(self, X):
                    rf_proba = self.rf.predict_proba(X)
                    gb_proba = self.gb.predict_proba(X)
                    return (rf_proba + gb_proba) / 2
                
                def predict(self, X):
                    return (self.predict_proba(X)[:, 1] > 0.5).astype(int)
            
            self.model = EnsembleModel(rf_model, gb_model)
            
            # Оценка качества
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]
            y_pred = self.model.predict(X_test)
            
            accuracy = accuracy_score(y_test, y_pred)
            roc_auc = roc_auc_score(y_test, y_pred_proba)
            
            # Кросс-валидация
            cv_scores = cross_val_score(rf_model, X_scaled, y, cv=5, scoring='roc_auc')
            
            self.is_trained = True
            
            # Сохраняем модель
            self._save_model()
            
            # Получаем важность признаков
            feature_importance = self._get_feature_importance()
            
            result = {
                "status": "trained",
                "samples_used": len(df),
                "real_samples": len(df_real),
                "synthetic_samples": len(df) - len(df_real) if len(df_real) > 0 else len(df),
                "accuracy": round(accuracy, 3),
                "roc_auc": round(roc_auc, 3),
                "cv_auc_mean": round(np.mean(cv_scores), 3),
                "cv_auc_std": round(np.std(cv_scores), 3),
                "feature_importance": feature_importance[:10],  # Топ 10
                "message": f"Модель обучена! AUC ROC: {roc_auc:.3f}"
            }
            
            print(f"✅ {result['message']}")
            return result
            
        except Exception as e:
            print(f"❌ Ошибка обучения: {e}")
            import traceback
            traceback.print_exc()
            
            # Создаём простую эвристическую модель как fallback
            self._create_fallback_model()
            
            return {
                "status": "fallback",
                "error": str(e),
                "message": "Создана эвристическая модель как запасной вариант"
            }
    
    def _create_fallback_model(self):
        """Создание эвристической модели на основе правил"""
        self.is_trained = True
        self.model = "heuristic"
        print("ℹСоздана эвристическая модель (запасной вариант)")
    
    def _get_feature_importance(self) -> List[Dict[str, Any]]:
        """Получение важности признаков"""
        if not self.is_trained or self.model == "heuristic":
            # Дефолтная важность для эвристической модели
            default_importance = [
                {"feature": "view_count", "importance": 0.25},
                {"feature": "application_count", "importance": 0.20},
                {"feature": "contact_rate", "importance": 0.15},
                {"feature": "competition_ratio", "importance": 0.12},
                {"feature": "price_per_sqm", "importance": 0.10},
                {"feature": "views_last_30d", "importance": 0.08},
                {"feature": "is_free", "importance": 0.05},
                {"feature": "has_active_contract", "importance": 0.05}
            ]
            return default_importance
        
        try:
            # Берём важность из RandomForest
            rf_model = self.model.rf
            importance = rf_model.feature_importances_
            
            features = []
            for name, imp in zip(self.feature_columns, importance):
                features.append({"feature": name, "importance": round(float(imp), 4)})
            
            return sorted(features, key=lambda x: x['importance'], reverse=True)
        except Exception as e:
            print(f"Ошибка получения важности признаков: {e}")
            return []
    
    def predict_probability(self, conn, office_id: int) -> Dict[str, Any]:
        """
        Прогноз вероятности аренды для конкретного офиса
        
        Args:
            conn: PostgreSQL соединение
            office_id: ID офиса
        
        Returns:
            Dict с прогнозом
        """
        if not self.is_trained:
            # Если модель не обучена, обучаем
            self.train(conn)
        
        try:
            # Получаем признаки для офиса
            df = self._extract_features_from_db(conn, [office_id])
            
            if len(df) == 0:
                return {"error": f"Офис {office_id} не найден"}
            
            # Эвристический прогноз если модель не готова
            if self.model == "heuristic":
                return self._heuristic_prediction(df.iloc[0])
            
            # Нормализация
            X = df[self.feature_columns].values
            X_scaled = self.scaler.transform(X)
            
            # Прогноз
            probability = float(self.model.predict_proba(X_scaled)[0, 1])
            
            # Определяем категорию
            if probability >= 0.7:
                category = "high"
                description = "Высокая вероятность аренды в этом месяце"
            elif probability >= 0.4:
                category = "medium"
                description = "Средняя вероятность аренды в этом месяце"
            else:
                category = "low"
                description = "Низкая вероятность аренды в этом месяце"
            
            # Топ факторов
            top_factors = self._get_feature_importance()[:3]
            
            return {
                "office_id": office_id,
                "probability": probability,
                "probability_percent": round(probability * 100, 1),
                "category": category,
                "description": description,
                "top_factors": top_factors,
                "model_type": "ml_ensemble" if self.model != "heuristic" else "heuristic"
            }
            
        except Exception as e:
            print(f"Ошибка прогноза: {e}")
            return self._heuristic_prediction_from_db(conn, office_id)
    
    def _heuristic_prediction(self, row: pd.Series) -> Dict[str, Any]:
        """Эвристический прогноз на основе правил"""
        score = 0
        
        # Просмотры
        if row.get('view_count', 0) >= 10:
            score += 0.3
        elif row.get('view_count', 0) >= 5:
            score += 0.15
        
        # Контакты
        if row.get('contact_rate', 0) >= 0.3:
            score += 0.25
        elif row.get('contact_rate', 0) >= 0.15:
            score += 0.12
        
        # Заявки
        if row.get('application_count', 0) >= 3:
            score += 0.25
        elif row.get('application_count', 0) >= 1:
            score += 0.12
        
        # Конкуренция
        if row.get('competition_ratio', 1) < 0.3:
            score += 0.2
        
        probability = min(0.95, score)
        
        if probability >= 0.7:
            category = "high"
        elif probability >= 0.4:
            category = "medium"
        else:
            category = "low"
        
        return {
            "office_id": int(row.get('office_id', 0)),
            "probability": probability,
            "probability_percent": round(probability * 100, 1),
            "category": category,
            "description": f"{category.capitalize()} вероятность аренды (эвристика)",
            "top_factors": self._get_feature_importance()[:3],
            "model_type": "heuristic"
        }
    
    def _heuristic_prediction_from_db(self, conn, office_id: int) -> Dict[str, Any]:
        """Эвристический прогноз напрямую из БД"""
        cursor = conn.cursor()
        
        # Собираем статистику
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM office_views WHERE office_id = %s) as views,
                (SELECT COUNT(*) FROM applications WHERE office_id = %s) as apps,
                (SELECT COALESCE(AVG(CASE WHEN is_contacted THEN 1 ELSE 0 END), 0) 
                 FROM office_views WHERE office_id = %s) as contact_rate,
                (SELECT COUNT(*) FROM offices WHERE floor = (SELECT floor FROM offices WHERE id = %s) AND is_free = TRUE) as free_on_floor,
                (SELECT COUNT(*) FROM offices WHERE floor = (SELECT floor FROM offices WHERE id = %s)) as total_on_floor
        """, (office_id, office_id, office_id, office_id, office_id))
        
        stats = cursor.fetchone()
        cursor.close()
        
        views = stats['views'] or 0
        apps = stats['apps'] or 0
        contact_rate = stats['contact_rate'] or 0
        competition = stats['free_on_floor'] / stats['total_on_floor'] if stats['total_on_floor'] > 0 else 1
        
        score = 0
        if views >= 10:
            score += 0.3
        elif views >= 5:
            score += 0.15
        
        if contact_rate >= 0.3:
            score += 0.25
        elif contact_rate >= 0.15:
            score += 0.12
        
        if apps >= 3:
            score += 0.25
        elif apps >= 1:
            score += 0.12
        
        if competition < 0.3:
            score += 0.2
        
        probability = min(0.95, score)
        
        if probability >= 0.7:
            category = "high"
        elif probability >= 0.4:
            category = "medium"
        else:
            category = "low"
        
        return {
            "office_id": office_id,
            "probability": probability,
            "probability_percent": round(probability * 100, 1),
            "category": category,
            "description": f"{category.capitalize()} вероятность аренды (на основе статистики)",
            "top_factors": self._get_feature_importance()[:3],
            "model_type": "heuristic"
        }
    
    def predict_batch(self, conn, office_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Массовый прогноз для нескольких офисов
        
        Args:
            conn: PostgreSQL соединение
            office_ids: Список ID офисов
        
        Returns:
            List[Dict] с прогнозами
        """
        results = []
        for office_id in office_ids:
            result = self.predict_probability(conn, office_id)
            results.append(result)
        
        # Сортируем по вероятности
        results.sort(key=lambda x: x.get('probability', 0), reverse=True)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели"""
        return {
            "is_trained": self.is_trained,
            "model_type": "ensemble_rf_gb" if self.model and self.model != "heuristic" else "heuristic",
            "feature_count": len(self.feature_columns) if self.feature_columns else 0,
            "features": self.feature_columns[:10] if self.feature_columns else [],
            "feature_importance": self._get_feature_importance()[:5]
        }


# Глобальный экземпляр
rental_predictor = OfficeRentalPredictor()