
# backend/api/ml_models/monitoring/metrics.py
"""
Мониторинг качества модели
"""
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
import json
import logging

logger = logging.getLogger(__name__)


class ModelMonitor:
    """
    Мониторинг модели в production
    
    Отслеживает:
    - Количество предсказаний
    - Распределение вероятностей
    - Дрейф данных
    - Точность (при наличии фидбека)
    """
    
    def __init__(self, max_history: int = 10000):
        self.predictions_history = deque(maxlen=max_history)
        self.feedback_history = deque(maxlen=max_history)
        self.daily_stats = {}
    
    def log_prediction(self, office_id: int, probability: float, features: Optional[Dict] = None):
        """Логирование предсказания"""
        self.predictions_history.append({
            'timestamp': datetime.now(),
            'office_id': office_id,
            'probability': probability,
            'features': features
        })
    
    def log_feedback(self, office_id: int, actual_rented: bool, predicted_probability: float):
        """Логирование обратной связи (была ли реальная аренда)"""
        self.feedback_history.append({
            'timestamp': datetime.now(),
            'office_id': office_id,
            'actual': actual_rented,
            'predicted': predicted_probability
        })
    
    def get_daily_stats(self) -> Dict[str, Any]:
        """Получение дневной статистики"""
        today = datetime.now().date()
        
        if today in self.daily_stats:
            return self.daily_stats[today]
        
        # Предсказания за сегодня
        today_preds = [
            p for p in self.predictions_history
            if p['timestamp'].date() == today
        ]
        
        stats = {
            'date': today.isoformat(),
            'total_predictions': len(today_preds),
            'avg_probability': np.mean([p['probability'] for p in today_preds]) if today_preds else 0,
            'high_probability_count': len([p for p in today_preds if p['probability'] >= 0.7]),
            'medium_probability_count': len([p for p in today_preds if 0.4 <= p['probability'] < 0.7]),
            'low_probability_count': len([p for p in today_preds if p['probability'] < 0.4])
        }
        
        # Добавляем точность, если есть фидбек
        today_feedback = [
            f for f in self.feedback_history
            if f['timestamp'].date() == today
        ]
        
        if today_feedback:
            correct = sum(
                1 for f in today_feedback
                if (f['actual'] and f['predicted'] >= 0.5) or (not f['actual'] and f['predicted'] < 0.5)
            )
            stats['accuracy'] = correct / len(today_feedback)
        
        self.daily_stats[today] = stats
        return stats
    
    def detect_data_drift(self, current_distribution: np.ndarray, reference_distribution: np.ndarray) -> Dict[str, Any]:
        """
        Обнаружение дрейфа данных с помощью KS-теста
        """
        from scipy import stats
        
        if len(current_distribution) < 10 or len(reference_distribution) < 10:
            return {"drift_detected": False, "reason": "Insufficient data"}
        
        # KS-тест для каждого признака
        drift_results = {}
        for i in range(min(current_distribution.shape[1], reference_distribution.shape[1])):
            ks_stat, p_value = stats.ks_2samp(
                current_distribution[:, i],
                reference_distribution[:, i]
            )
            
            drift_results[f'feature_{i}'] = {
                'ks_statistic': float(ks_stat),
                'p_value': float(p_value),
                'drift_detected': p_value < 0.05
            }
        
        # Общий дрейф
        total_drift_features = sum(1 for r in drift_results.values() if r['drift_detected'])
        drift_detected = total_drift_features > (len(drift_results) * 0.3)  # 30% признаков
        
        return {
            'drift_detected': drift_detected,
            'drift_ratio': total_drift_features / len(drift_results) if drift_results else 0,
            'features': drift_results
        }
    
    def get_alert(self) -> Optional[Dict[str, Any]]:
        """
        Проверка необходимости алерта
        """
        stats = self.get_daily_stats()
        
        # Алерт при падении точности
        if 'accuracy' in stats and stats['accuracy'] < 0.6:
            return {
                'level': 'warning',
                'message': f"Model accuracy dropped to {stats['accuracy']:.2%}",
                'metric': 'accuracy',
                'value': stats['accuracy']
            }
        
        # Алерт при аномальном распределении вероятностей
        if stats['total_predictions'] > 10:
            high_ratio = stats['high_probability_count'] / stats['total_predictions']
            if high_ratio > 0.8:
                return {
                    'level': 'info',
                    'message': f"Unusual distribution: {high_ratio:.1%} high probability predictions",
                    'metric': 'high_probability_ratio',
                    'value': high_ratio
                }
        
        return None