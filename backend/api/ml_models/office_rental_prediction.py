# backend/api/ml_models/office_rental_prediction.py
"""
Адаптер для роутера ai_rental_prediction
Обеспечивает обратную совместимость с существующим API
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

# Импортируем production predictor
from .predictor import production_predictor
from .feature_extractor import feature_extractor

logger = logging.getLogger(__name__)


class RentalPredictor:
    """
    Класс-адаптер, который предоставляет интерфейс,
    ожидаемый роутером ai_rental_prediction
    """
    
    def __init__(self):
        self._predictor = production_predictor
    
    def train(self, conn, force_retrain: bool = False) -> Dict[str, Any]:
        """
        Обучение модели
        
        Args:
            conn: PostgreSQL соединение
            force_retrain: Принудительное переобучение
        
        Returns:
            Dict с результатами обучения
        """
        return self._predictor.train(conn, force_retrain)
    
    def predict_probability(self, conn, office_id: int) -> Dict[str, Any]:
        """
        Предсказание вероятности аренды для офиса
        
        Args:
            conn: PostgreSQL соединение
            office_id: ID офиса
        
        Returns:
            Dict с предсказанием
        """
        result = self._predictor.predict(conn, office_id)
        
        # Добавляем поля, которые ожидает роутер
        if "error" not in result:
            probability = result.get("probability", 0.5)
            
            # Определяем категорию
            if probability >= 0.7:
                category = "high"
                description = "Высокая вероятность аренды! Офис востребован."
            elif probability >= 0.4:
                category = "medium"
                description = "Средняя вероятность аренды. Есть потенциал."
            else:
                category = "low"
                description = "Низкая вероятность аренды. Требуется анализ."
            
            # Добавляем топ факторов (из feature importance если есть)
            model_info = self._predictor.get_model_info()
            top_factors = []
            
            if model_info.get('metadata', {}).get('feature_importance'):
                for feat in model_info['metadata']['feature_importance'][:5]:
                    top_factors.append({
                        "feature": feat.get('name', f"feature_{feat.get('feature_index', 0)}"),
                        "importance": feat.get('importance', 0)
                    })
            
            result.update({
                "category": category,
                "description": description,
                "top_factors": top_factors
            })
        
        return result
    
    def predict_batch(self, conn, office_ids: List[int]) -> List[Dict[str, Any]]:
        """Массовое предсказание"""
        return self._predictor.predict_batch(conn, office_ids)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Информация о модели"""
        return self._predictor.get_model_info()
    
    @property
    def is_trained(self) -> bool:
        return self._predictor.is_trained


# Глобальный экземпляр для импорта в роутер
rental_predictor = RentalPredictor()