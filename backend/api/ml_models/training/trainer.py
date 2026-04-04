# backend/api/ml_models/training/trainer.py
"""
Централизованный тренировщик моделей
Координирует обучение, валидацию, оптимизацию гиперпараметров и сохранение
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
from sklearn.calibration import calibration_curve
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from ..config import config
from ..models.ensemble import EnsembleModel
from ..models.neural import neural_predictor, NeuralNetworkConfig
from .synthetic import data_generator, target_generator

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Главный тренировщик моделей
    
    Особенности:
    - Кросс-валидация
    - Поиск гиперпараметров (Grid Search / Random Search)
    - Ансамблирование моделей
    - Калибровка вероятностей
    - Сохранение метаданных
    """
    
    def __init__(self):
        self.models = {}
        self.best_model = None
        self.cv_results = {}
        self.hyperparameter_search_results = {}
        self.calibration_model = None
        self.training_metadata = {}
        
    def train_with_cross_validation(self,
                                   X: np.ndarray,
                                   y: np.ndarray,
                                   model_type: str = 'ensemble',
                                   n_folds: int = 5,
                                   use_synthetic: bool = True) -> Dict[str, Any]:
        """
        Обучение с кросс-валидацией
        
        Args:
            X: Признаки
            y: Целевая переменная
            model_type: Тип модели ('ensemble', 'neural', 'all')
            n_folds: Количество фолдов
            use_synthetic: Использовать синтетические данные при дисбалансе
        
        Returns:
            Dict с результатами кросс-валидации
        """
        logger.info(f"Starting {n_folds}-fold cross-validation for {model_type}")
        
        # Проверяем дисбаланс классов
        pos_ratio = y.mean()
        logger.info(f"Positive class ratio: {pos_ratio:.3f}")
        
        # При сильном дисбалансе генерируем синтетические данные
        if use_synthetic and (pos_ratio < 0.1 or pos_ratio > 0.9):
            logger.info("Class imbalance detected, generating synthetic data...")
            X, y = self._balance_with_synthetic_data(X, y, target_ratio=0.3)
            logger.info(f"Dataset size after balancing: {len(X)} samples")
        
        # Stratified K-Fold для сохранения распределения классов
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=config.RANDOM_STATE)
        
        cv_scores = {
            'fold': [],
            'roc_auc': [],
            'accuracy': [],
            'precision': [],
            'recall': [],
            'f1': []
        }
        
        models_by_fold = []
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
            logger.info(f"Training fold {fold}/{n_folds}")
            
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Обучаем модель на этом фолде
            if model_type == 'ensemble':
                model = EnsembleModel(random_state=config.RANDOM_STATE + fold)
                train_result = model.train(X_train, y_train)
                
            elif model_type == 'neural':
                # Разделяем train на train/val для нейросети
                X_train_nn, X_val_nn, y_train_nn, y_val_nn = train_test_split(
                    X_train, y_train, test_size=0.2, random_state=config.RANDOM_STATE
                )
                
                nn_config = NeuralNetworkConfig(
                    input_dim=X_train.shape[1],
                    hidden_dims=[128, 64, 32],
                    dropout_rate=0.3,
                    epochs=50,
                    early_stopping_patience=10
                )
                
                train_result = neural_predictor.train(
                    X_train_nn, y_train_nn, X_val_nn, y_val_nn, nn_config
                )
                model = neural_predictor
                
            else:
                # Обучаем оба и ансамблируем
                ensemble_model = EnsembleModel(random_state=config.RANDOM_STATE + fold)
                ensemble_model.train(X_train, y_train)
                
                nn_config = NeuralNetworkConfig(input_dim=X_train.shape[1])
                neural_predictor.train(X_train, y_train, X_val, y_val, nn_config)
                
                # Создаем ансамбль
                model = self._create_hybrid_model(ensemble_model, neural_predictor)
            
            # Предсказания на валидации
            if model_type == 'neural':
                y_pred_proba = model.predict_proba(X_val)
            else:
                y_pred_proba = model.predict_proba(X_val)[:, 1]
            
            y_pred = (y_pred_proba > 0.5).astype(int)
            
            # Сохраняем метрики
            cv_scores['fold'].append(fold)
            cv_scores['roc_auc'].append(roc_auc_score(y_val, y_pred_proba))
            cv_scores['accuracy'].append(accuracy_score(y_val, y_pred))
            cv_scores['precision'].append(precision_score(y_val, y_pred, zero_division=0))
            cv_scores['recall'].append(recall_score(y_val, y_pred, zero_division=0))
            cv_scores['f1'].append(f1_score(y_val, y_pred, zero_division=0))
            
            models_by_fold.append(model)
            
            logger.info(f"  Fold {fold} - AUC: {cv_scores['roc_auc'][-1]:.3f}, F1: {cv_scores['f1'][-1]:.3f}")
        
        # Сохраняем результаты
        self.cv_results = cv_scores
        
        # Выбираем лучшую модель
        best_fold_idx = np.argmax(cv_scores['roc_auc'])
        self.best_model = models_by_fold[best_fold_idx]
        
        # Обучаем финальную модель на всех данных
        logger.info("Training final model on all data...")
        if model_type == 'ensemble':
            final_model = EnsembleModel(random_state=config.RANDOM_STATE)
            final_model.train(X, y)
        elif model_type == 'neural':
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=config.RANDOM_STATE
            )
            nn_config = NeuralNetworkConfig(input_dim=X.shape[1])
            neural_predictor.train(X_train, y_train, X_val, y_val, nn_config)
            final_model = neural_predictor
        else:
            final_model = self._create_hybrid_model(
                EnsembleModel(random_state=config.RANDOM_STATE),
                neural_predictor
            )
            final_model.train(X, y)
        
        self.best_model = final_model
        
        # Калибровка вероятностей
        self._calibrate_model(X, y)
        
        # Сохраняем метаданные
        self.training_metadata = {
            'model_type': model_type,
            'n_folds': n_folds,
            'cv_results': {
                'mean_auc': float(np.mean(cv_scores['roc_auc'])),
                'std_auc': float(np.std(cv_scores['roc_auc'])),
                'mean_f1': float(np.mean(cv_scores['f1'])),
                'std_f1': float(np.std(cv_scores['f1']))
            },
            'best_fold': best_fold_idx + 1,
            'samples_count': len(X),
            'positive_ratio': float(y.mean()),
            'trained_at': datetime.now().isoformat()
        }
        
        logger.info(f"CV complete. Mean AUC: {self.training_metadata['cv_results']['mean_auc']:.3f} ± {self.training_metadata['cv_results']['std_auc']:.3f}")
        
        return self.training_metadata
    
    def _balance_with_synthetic_data(self, 
                                     X: np.ndarray, 
                                     y: np.ndarray, 
                                     target_ratio: float = 0.3) -> Tuple[np.ndarray, np.ndarray]:
        """
        Балансировка классов с помощью синтетических данных
        """
        # Обучаем генераторы на реальных данных
        data_generator.fit(X, [f'feature_{i}' for i in range(X.shape[1])])
        target_generator.fit(X, y)
        
        # Определяем, сколько синтетических данных нужно
        current_pos = y.sum()
        current_neg = len(y) - current_pos
        
        if target_ratio > 0.5:
            target_pos = int(len(y) * target_ratio)
            synthetic_needed = max(0, target_pos - current_pos)
        else:
            target_neg = int(len(y) * (1 - target_ratio))
            synthetic_needed = max(0, target_neg - current_neg)
        
        if synthetic_needed > 0:
            # Генерируем синтетические данные
            X_synth = data_generator.generate(synthetic_needed).values
            y_synth = target_generator.generate(X_synth)
            
            # Объединяем с реальными
            X_balanced = np.vstack([X, X_synth])
            y_balanced = np.hstack([y, y_synth])
            
            logger.info(f"Added {synthetic_needed} synthetic samples")
            logger.info(f"New positive ratio: {y_balanced.mean():.3f}")
            
            return X_balanced, y_balanced
        
        return X, y
    
    def _create_hybrid_model(self, ensemble_model, neural_model):
        """
        Создание гибридной модели (ансамбль + нейросеть)
        """
        class HybridModel:
            def __init__(self, ensemble, neural):
                self.ensemble = ensemble
                self.neural = neural
                self.ensemble_weight = 0.6
                self.neural_weight = 0.4
            
            def train(self, X, y):
                # Оба уже обучены
                pass
            
            def predict_proba(self, X):
                ensemble_proba = self.ensemble.predict_proba(X)[:, 1]
                neural_proba = self.neural.predict_proba(X)
                
                # Взвешенное усреднение
                hybrid_proba = (self.ensemble_weight * ensemble_proba + 
                               self.neural_weight * neural_proba)
                
                return np.column_stack([1 - hybrid_proba, hybrid_proba])
            
            def predict(self, X, threshold=0.5):
                proba = self.predict_proba(X)[:, 1]
                return (proba > threshold).astype(int)
        
        return HybridModel(ensemble_model, neural_model)
    
    def _calibrate_model(self, X: np.ndarray, y: np.ndarray):
        """
        Калибровка вероятностей с использованием Platt Scaling или Isotonic Regression
        """
        from sklearn.calibration import CalibratedClassifierCV
        
        logger.info("Calibrating model probabilities...")
        
        # Создаем обёртку для калибровки
        class ModelWrapper:
            def __init__(self, model):
                self.model = model
            
            def fit(self, X, y):
                # Модель уже обучена
                pass
            
            def predict_proba(self, X):
                return self.model.predict_proba(X)
        
        # Используем кросс-валидацию для калибровки
        calibrated_model = CalibratedClassifierCV(
            ModelWrapper(self.best_model),
            method='sigmoid',  # Platt scaling
            cv=5
        )
        
        # Обучаем калибратор
        calibrated_model.fit(X, y)
        
        # Проверяем улучшение
        original_proba = self.best_model.predict_proba(X)[:, 1]
        calibrated_proba = calibrated_model.predict_proba(X)[:, 1]
        
        original_auc = roc_auc_score(y, original_proba)
        calibrated_auc = roc_auc_score(y, calibrated_proba)
        
        logger.info(f"Calibration: AUC improved from {original_auc:.3f} to {calibrated_auc:.3f}")
        
        self.calibration_model = calibrated_model
        
        # Обновляем лучшую модель
        self.best_model = calibrated_model
    
    def hyperparameter_search(self,
                             X: np.ndarray,
                             y: np.ndarray,
                             model_type: str = 'ensemble',
                             search_type: str = 'random',
                             n_iter: int = 20) -> Dict[str, Any]:
        """
        Поиск гиперпараметров
        
        Args:
            X: Признаки
            y: Целевая переменная
            model_type: Тип модели
            search_type: 'grid' или 'random'
            n_iter: Количество итераций для random search
        
        Returns:
            Dict с лучшими параметрами
        """
        from sklearn.model_selection import RandomizedSearchCV, GridSearchCV
        
        logger.info(f"Starting hyperparameter search for {model_type}")
        
        if model_type == 'ensemble':
            from sklearn.ensemble import RandomForestClassifier
            
            base_model = RandomForestClassifier(random_state=config.RANDOM_STATE)
            
            param_grid = {
                'n_estimators': [50, 100, 200, 300],
                'max_depth': [5, 7, 10, 15, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'max_features': ['sqrt', 'log2', None]
            }
        elif model_type == 'xgboost':
            import xgboost as xgb
            
            base_model = xgb.XGBClassifier(random_state=config.RANDOM_STATE)
            
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 5, 7, 9],
                'learning_rate': [0.01, 0.05, 0.1, 0.3],
                'subsample': [0.6, 0.8, 1.0],
                'colsample_bytree': [0.6, 0.8, 1.0]
            }
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # Выбираем метод поиска
        if search_type == 'grid':
            search = GridSearchCV(
                base_model,
                param_grid,
                cv=5,
                scoring='roc_auc',
                n_jobs=-1,
                verbose=1
            )
        else:
            search = RandomizedSearchCV(
                base_model,
                param_grid,
                n_iter=n_iter,
                cv=5,
                scoring='roc_auc',
                random_state=config.RANDOM_STATE,
                n_jobs=-1,
                verbose=1
            )
        
        # Запускаем поиск
        search.fit(X, y)
        
        # Сохраняем результаты
        self.hyperparameter_search_results = {
            'model_type': model_type,
            'search_type': search_type,
            'best_params': search.best_params_,
            'best_score': float(search.best_score_),
            'cv_results': {
                'mean_test_score': [float(x) for x in search.cv_results_['mean_test_score']],
                'std_test_score': [float(x) for x in search.cv_results_['std_test_score']]
            }
        }
        
        logger.info(f"Best parameters: {search.best_params_}")
        logger.info(f"Best CV score: {search.best_score_:.4f}")
        
        return self.hyperparameter_search_results
    
    def evaluate_model(self,
                      X_test: np.ndarray,
                      y_test: np.ndarray,
                      model = None) -> Dict[str, Any]:
        """
        Детальная оценка модели
        
        Args:
            X_test: Тестовые признаки
            y_test: Тестовые целевые значения
            model: Модель для оценки (если None, использует best_model)
        
        Returns:
            Dict с метриками
        """
        if model is None:
            model = self.best_model
        
        if model is None:
            raise ValueError("No model available for evaluation")
        
        # Предсказания
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # Основные метрики
        metrics = {
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0)
        }
        
        # Дополнительные метрики
        from sklearn.metrics import (
            average_precision_score, brier_score_loss,
            log_loss, matthews_corrcoef
        )
        
        metrics['average_precision'] = average_precision_score(y_test, y_pred_proba)
        metrics['brier_score'] = brier_score_loss(y_test, y_pred_proba)
        metrics['log_loss'] = log_loss(y_test, y_pred_proba)
        metrics['matthews_corrcoef'] = matthews_corrcoef(y_test, y_pred)
        
        # Калибровка
        prob_true, prob_pred = calibration_curve(y_test, y_pred_proba, n_bins=10)
        metrics['calibration_error'] = np.mean(np.abs(prob_true - prob_pred))
        
        # Статистика по вероятностям
        metrics['probability_stats'] = {
            'mean': float(np.mean(y_pred_proba)),
            'std': float(np.std(y_pred_proba)),
            'min': float(np.min(y_pred_proba)),
            'max': float(np.max(y_pred_proba)),
            'q25': float(np.percentile(y_pred_proba, 25)),
            'q50': float(np.percentile(y_pred_proba, 50)),
            'q75': float(np.percentile(y_pred_proba, 75))
        }
        
        # Матрица ошибок
        from sklearn.metrics import confusion_matrix
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        
        metrics['confusion_matrix'] = {
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp)
        }
        
        logger.info("=" * 50)
        logger.info("MODEL EVALUATION RESULTS")
        logger.info(f"ROC AUC: {metrics['roc_auc']:.4f}")
        logger.info(f"F1 Score: {metrics['f1_score']:.4f}")
        logger.info(f"Precision: {metrics['precision']:.4f}")
        logger.info(f"Recall: {metrics['recall']:.4f}")
        logger.info(f"Calibration Error: {metrics['calibration_error']:.4f}")
        logger.info("=" * 50)
        
        return metrics
    
    def save_training_report(self, report_path: Optional[Path] = None) -> str:
        """
        Сохранение полного отчёта о обучении
        """
        if report_path is None:
            report_path = config.LOG_DIR / f'training_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        report = {
            'training_metadata': self.training_metadata,
            'cv_results': self.cv_results,
            'hyperparameter_search': self.hyperparameter_search_results,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Training report saved to {report_path}")
        return str(report_path)
    
    def compare_models(self,
                      X_test: np.ndarray,
                      y_test: np.ndarray,
                      models: Dict[str, Any]) -> pd.DataFrame:
        """
        Сравнение нескольких моделей
        """
        results = []
        
        for name, model in models.items():
            metrics = self.evaluate_model(X_test, y_test, model)
            metrics['model_name'] = name
            results.append(metrics)
        
        df = pd.DataFrame(results)
        df = df.set_index('model_name')
        
        # Сортируем по ROC AUC
        df = df.sort_values('roc_auc', ascending=False)
        
        logger.info("\nModel Comparison:")
        print(df[['roc_auc', 'f1_score', 'precision', 'recall']].round(4))
        
        return df


# Глобальный экземпляр
model_trainer = ModelTrainer()