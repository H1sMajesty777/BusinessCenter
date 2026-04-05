# backend/api/ml_models/models/ensemble.py
"""
Ансамблевая модель для предсказания аренды
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.model_selection import train_test_split
import xgboost as xgb
import lightgbm as lgb
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


class EnsembleModel:
    """
    Ансамбль моделей для предсказания аренды
    
    Модели:
    - Random Forest
    - XGBoost
    - LightGBM
    - Gradient Boosting
    """
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.scaler = RobustScaler()
        self.model = None
        self.feature_importance = None
        self.is_fitted = False
    
    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """
        Обучение ансамбля
        
        Args:
            X: Признаки
            y: Целевая переменная
        
        Returns:
            Dict с метриками
        """
        logger.info(f"Training ensemble on {len(X)} samples with {X.shape[1]} features")
        
        # Нормализация
        X_scaled = self.scaler.fit_transform(X)
        
        # Разделение на train/val
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, test_size=0.2, random_state=self.random_state, stratify=y
        )
        
        # Создаём модели
        models = [
            ('rf', RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=self.random_state,
                n_jobs=-1
            )),
            ('xgb', xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=self.random_state,
                use_label_encoder=False,
                eval_metric='logloss'
            )),
            ('lgb', lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=self.random_state,
                verbose=-1
            )),
            ('gb', GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=self.random_state
            ))
        ]
        
        # Создаём voting classifier
        self.model = VotingClassifier(
            estimators=models,
            voting='soft',  # soft voting использует вероятности
            weights=[1, 1, 1, 1]  # равные веса
        )
        
        # Обучаем
        self.model.fit(X_train, y_train)
        
        # Оценка на валидации
        y_pred_proba = self.model.predict_proba(X_val)[:, 1]
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        metrics = {
            'roc_auc': roc_auc_score(y_val, y_pred_proba),
            'average_precision': average_precision_score(y_val, y_pred_proba),
            'brier_score': brier_score_loss(y_val, y_pred_proba),
            'accuracy': (y_pred == y_val).mean()
        }
        
        # Кросс-валидация
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5, scoring='roc_auc')
        metrics['cv_auc_mean'] = cv_scores.mean()
        metrics['cv_auc_std'] = cv_scores.std()
        
        # Важность признаков (усредняем по всем моделям)
        self.feature_importance = self._calculate_feature_importance()
        
        self.is_fitted = True
        
        logger.info(f"Ensemble trained. AUC: {metrics['roc_auc']:.3f}, CV AUC: {metrics['cv_auc_mean']:.3f}")
        
        return {
            'metrics': metrics,
            'feature_importance': self.feature_importance[:10]
        }
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Предсказание вероятностей"""
        if not self.is_fitted:
            raise ValueError("Model not fitted yet")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Бинарное предсказание"""
        proba = self.predict_proba(X)[:, 1]
        return (proba > threshold).astype(int)
    
    def _calculate_feature_importance(self) -> List[Dict[str, float]]:
        """Расчёт важности признаков"""
        importance_dict = {}
        
        for name, estimator in self.model.named_estimators_.items():
            if hasattr(estimator, 'feature_importances_'):
                imp = estimator.feature_importances_
                for i, val in enumerate(imp):
                    if name not in importance_dict:
                        importance_dict[name] = []
                    importance_dict[name].append(val)
        
        # Усредняем по всем моделям
        if importance_dict:
            avg_importance = np.mean(list(importance_dict.values()), axis=0)
            
            features = []
            for i, imp in enumerate(avg_importance):
                features.append({
                    'feature_index': i,
                    'importance': float(imp)
                })
            
            return sorted(features, key=lambda x: x['importance'], reverse=True)
        
        return []