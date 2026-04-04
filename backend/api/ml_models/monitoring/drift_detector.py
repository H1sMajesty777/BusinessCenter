# backend/api/ml_models/monitoring/drift_detector.py
"""
Обнаружение дрейфа данных (Data Drift Detection)
Для мониторинга качества модели в production
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
from scipy import stats
from scipy.spatial.distance import jensenshannon
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class DriftReport:
    """Отчет о дрейфе данных"""
    drift_detected: bool
    drift_severity: str  # 'none', 'low', 'medium', 'high'
    affected_features: List[str]
    timestamp: datetime
    recommendations: List[str]


class DataDriftDetector:
    """
    Детектор дрейфа данных для ML моделей
    
    Отслеживает:
    - Дрейф признаков (Feature Drift)
    - Дрейф целевой переменной (Target Drift)
    - Дрейф концепции (Concept Drift)
    """
    
    def __init__(self, 
                 window_size: int = 1000,
                 reference_window_days: int = 30,
                 alert_threshold: float = 0.05):
        """
        Args:
            window_size: Размер окна для хранения данных
            reference_window_days: Размер референсного окна в днях
            alert_threshold: Порог для алерта (p-value < threshold)
        """
        self.window_size = window_size
        self.reference_window_days = reference_window_days
        self.alert_threshold = alert_threshold
        
        # Хранилище данных
        self.feature_history = deque(maxlen=window_size)
        self.prediction_history = deque(maxlen=window_size)
        self.target_history = deque(maxlen=window_size)
        
        # Референсные распределения
        self.reference_distributions = {}
        self.reference_target_distribution = None
        self.is_reference_set = False
        
        # Статистика дрейфа
        self.drift_history = deque(maxlen=100)
        
    def set_reference(self, features: np.ndarray, targets: Optional[np.ndarray] = None):
        """
        Установка референсного распределения (обычно на обучающих данных)
        
        Args:
            features: Матрица признаков для референса
            targets: Целевая переменная (опционально)
        """
        if len(features) == 0:
            logger.warning("Empty reference data provided")
            return
        
        # Сохраняем распределение для каждого признака
        for i in range(features.shape[1]):
            self.reference_distributions[f'feature_{i}'] = {
                'data': features[:, i].copy(),
                'mean': float(np.mean(features[:, i])),
                'std': float(np.std(features[:, i])),
                'quantiles': {
                    'q25': float(np.percentile(features[:, i], 25)),
                    'q50': float(np.percentile(features[:, i], 50)),
                    'q75': float(np.percentile(features[:, i], 75))
                }
            }
        
        if targets is not None:
            self.reference_target_distribution = {
                'data': targets.copy(),
                'positive_rate': float(np.mean(targets)),
                'count': len(targets)
            }
        
        self.is_reference_set = True
        logger.info(f"Reference distribution set with {len(features)} samples")
    
    def add_current_data(self, 
                         features: np.ndarray, 
                         predictions: np.ndarray,
                         targets: Optional[np.ndarray] = None):
        """
        Добавление текущих данных для мониторинга
        
        Args:
            features: Текущие признаки
            predictions: Предсказания модели
            targets: Реальные целевые значения (если известны)
        """
        for i in range(len(features)):
            self.feature_history.append({
                'timestamp': datetime.now(),
                'features': features[i].copy()
            })
            
            self.prediction_history.append({
                'timestamp': datetime.now(),
                'prediction': float(predictions[i])
            })
            
            if targets is not None:
                self.target_history.append({
                    'timestamp': datetime.now(),
                    'target': int(targets[i])
                })
    
    def detect_feature_drift(self, 
                            current_features: np.ndarray,
                            feature_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Обнаружение дрейфа признаков с помощью KS-теста и JS-дивергенции
        
        Args:
            current_features: Текущие признаки для проверки
            feature_names: Имена признаков (опционально)
        
        Returns:
            Dict с результатами детекции
        """
        if not self.is_reference_set:
            return {"error": "Reference distribution not set"}
        
        if len(current_features) == 0:
            return {"error": "No current data provided"}
        
        results = {}
        drift_count = 0
        
        for i in range(min(current_features.shape[1], len(self.reference_distributions))):
            feature_name = feature_names[i] if feature_names else f'feature_{i}'
            
            # Получаем референсные данные
            ref_data = self.reference_distributions[f'feature_{i}']['data']
            current_data = current_features[:, i]
            
            # KS-тест для проверки одинаковости распределений
            ks_stat, ks_pvalue = stats.ks_2samp(ref_data, current_data)
            
            # JS-дивергенция для измерения расстояния между распределениями
            # Создаем гистограммы для сравнения
            n_bins = min(50, min(len(ref_data), len(current_data)) // 10)
            if n_bins > 1:
                hist_ref, bins = np.histogram(ref_data, bins=n_bins, density=True)
                hist_curr, _ = np.histogram(current_data, bins=bins, density=True)
                js_divergence = jensenshannon(hist_ref + 1e-10, hist_curr + 1e-10)
            else:
                js_divergence = 0.0
            
            # Определяем severity
            drift_detected = ks_pvalue < self.alert_threshold
            if drift_detected:
                drift_count += 1
            
            if ks_pvalue < 0.01:
                severity = 'high'
            elif ks_pvalue < 0.05:
                severity = 'medium'
            elif ks_pvalue < 0.1:
                severity = 'low'
            else:
                severity = 'none'
            
            # Статистика изменений
            mean_change = (np.mean(current_data) - self.reference_distributions[f'feature_{i}']['mean']) / (self.reference_distributions[f'feature_{i}']['std'] + 1e-8)
            
            results[feature_name] = {
                'drift_detected': drift_detected,
                'severity': severity,
                'ks_statistic': float(ks_stat),
                'ks_pvalue': float(ks_pvalue),
                'js_divergence': float(js_divergence),
                'mean_change_std': float(mean_change),
                'reference_mean': self.reference_distributions[f'feature_{i}']['mean'],
                'current_mean': float(np.mean(current_data)),
                'reference_std': self.reference_distributions[f'feature_{i}']['std'],
                'current_std': float(np.std(current_data))
            }
        
        # Общий вывод
        drift_ratio = drift_count / len(results) if results else 0
        
        if drift_ratio > 0.5:
            overall_severity = 'high'
            recommendations = [
                "Значительный дрейф данных. Рекомендуется переобучение модели",
                "Проверьте изменения в бизнес-процессах",
                "Рассмотрите использование адаптивного обучения"
            ]
        elif drift_ratio > 0.3:
            overall_severity = 'medium'
            recommendations = [
                "Обнаружен умеренный дрейф данных",
                "Запланируйте переобучение модели в ближайшее время",
                "Проверьте корректность поступающих данных"
            ]
        elif drift_ratio > 0.1:
            overall_severity = 'low'
            recommendations = [
                "Незначительный дрейф данных. Продолжайте мониторинг",
                "Проверьте через 2 недели"
            ]
        else:
            overall_severity = 'none'
            recommendations = ["Дрейф данных не обнаружен. Модель стабильна"]
        
        return {
            'drift_detected': drift_count > 0,
            'drift_ratio': drift_ratio,
            'overall_severity': overall_severity,
            'affected_features_count': drift_count,
            'total_features': len(results),
            'features': results,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_target_drift(self, current_targets: np.ndarray) -> Dict[str, Any]:
        """
        Обнаружение дрейфа целевой переменной
        
        Args:
            current_targets: Текущие целевые значения
        """
        if not self.is_reference_set or self.reference_target_distribution is None:
            return {"error": "Reference target distribution not set"}
        
        if len(current_targets) == 0:
            return {"error": "No current targets provided"}
        
        current_positive_rate = np.mean(current_targets)
        ref_positive_rate = self.reference_target_distribution['positive_rate']
        
        # Тест пропорций
        from statsmodels.stats.proportion import proportions_ztest
        
        count = int(current_positive_rate * len(current_targets))
        nobs = len(current_targets)
        
        try:
            z_stat, p_value = proportions_ztest(
                count, nobs, 
                value=ref_positive_rate
            )
        except:
            p_value = 1.0
        
        drift_detected = p_value < self.alert_threshold
        rate_change = (current_positive_rate - ref_positive_rate) / (ref_positive_rate + 1e-8)
        
        if abs(rate_change) > 0.5:
            severity = 'high'
        elif abs(rate_change) > 0.3:
            severity = 'medium'
        elif abs(rate_change) > 0.1:
            severity = 'low'
        else:
            severity = 'none'
        
        return {
            'drift_detected': drift_detected,
            'severity': severity,
            'reference_positive_rate': float(ref_positive_rate),
            'current_positive_rate': float(current_positive_rate),
            'absolute_change': float(current_positive_rate - ref_positive_rate),
            'relative_change': float(rate_change),
            'p_value': float(p_value),
            'sample_size': len(current_targets),
            'recommendations': [
                "Целевая переменная изменилась. Рассмотрите переобучение" if drift_detected else "Распределение целевой переменной стабильно"
            ]
        }
    
    def detect_concept_drift(self, 
                            features: np.ndarray,
                            actual_targets: np.ndarray,
                            predicted_targets: np.ndarray) -> Dict[str, Any]:
        """
        Обнаружение дрейфа концепции (изменение связи features -> target)
        
        Использует:
        - Ошибки модели на новых данных
        - Сравнение с ожидаемой ошибкой
        """
        # Ошибки модели
        errors = (predicted_targets > 0.5) != (actual_targets > 0.5)
        current_error_rate = np.mean(errors)
        
        # Ожидаемая ошибка (из референса)
        if hasattr(self, 'reference_error_rate'):
            expected_error_rate = self.reference_error_rate
        else:
            expected_error_rate = 0.1  # Дефолтное значение
        
        # Проверка значимости увеличения ошибки
        error_increase = current_error_rate - expected_error_rate
        
        if error_increase > 0.15:
            severity = 'high'
            recommendations = [
                "Критический дрейф концепции! Модель устарела",
                "Немедленно переобучите модель",
                "Проверьте изменения в бизнес-правилах"
            ]
        elif error_increase > 0.08:
            severity = 'medium'
            recommendations = [
                "Обнаружен дрейф концепции",
                "Запланируйте переобучение модели",
                "Проверьте корректность предсказаний"
            ]
        elif error_increase > 0.03:
            severity = 'low'
            recommendations = [
                "Начальный дрейф концепции",
                "Продолжайте мониторинг"
            ]
        else:
            severity = 'none'
            recommendations = ["Дрейф концепции не обнаружен"]
        
        return {
            'drift_detected': error_increase > 0.05,
            'severity': severity,
            'current_error_rate': float(current_error_rate),
            'expected_error_rate': float(expected_error_rate),
            'error_increase': float(error_increase),
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_full_report(self, 
                       current_features: np.ndarray,
                       current_targets: Optional[np.ndarray] = None,
                       current_predictions: Optional[np.ndarray] = None,
                       feature_names: Optional[List[str]] = None) -> DriftReport:
        """
        Полный отчет о дрейфе данных
        """
        # Дрейф признаков
        feature_drift = self.detect_feature_drift(current_features, feature_names)
        
        # Дрейф целевой переменной
        target_drift = None
        if current_targets is not None:
            target_drift = self.detect_target_drift(current_targets)
        
        # Дрейф концепции
        concept_drift = None
        if current_targets is not None and current_predictions is not None:
            concept_drift = self.detect_concept_drift(
                current_features, current_targets, current_predictions
            )
        
        # Определяем общий severity
        severities = []
        if feature_drift.get('overall_severity') not in ['none', None]:
            severities.append(feature_drift['overall_severity'])
        if target_drift and target_drift.get('severity') not in ['none', None]:
            severities.append(target_drift['severity'])
        if concept_drift and concept_drift.get('severity') not in ['none', None]:
            severities.append(concept_drift['severity'])
        
        severity_weights = {'high': 3, 'medium': 2, 'low': 1}
        if severities:
            max_severity = max(severities, key=lambda s: severity_weights.get(s, 0))
        else:
            max_severity = 'none'
        
        # Собираем все рекомендации
        all_recommendations = []
        if feature_drift.get('recommendations'):
            all_recommendations.extend(feature_drift['recommendations'])
        if target_drift and target_drift.get('recommendations'):
            all_recommendations.extend(target_drift['recommendations'])
        if concept_drift and concept_drift.get('recommendations'):
            all_recommendations.extend(concept_drift['recommendations'])
        
        # Определяем, какие признаки затронуты
        affected_features = []
        if 'features' in feature_drift:
            affected_features = [
                name for name, data in feature_drift['features'].items()
                if data.get('drift_detected', False)
            ]
        
        drift_detected = (
            feature_drift.get('drift_detected', False) or
            (target_drift and target_drift.get('drift_detected', False)) or
            (concept_drift and concept_drift.get('drift_detected', False))
        )
        
        # Сохраняем в историю
        self.drift_history.append({
            'timestamp': datetime.now(),
            'drift_detected': drift_detected,
            'severity': max_severity,
            'affected_features_count': len(affected_features)
        })
        
        return DriftReport(
            drift_detected=drift_detected,
            drift_severity=max_severity,
            affected_features=affected_features,
            timestamp=datetime.now(),
            recommendations=all_recommendations[:5]  # Топ 5 рекомендаций
        )
    
    def get_drift_trend(self, days: int = 30) -> Dict[str, Any]:
        """
        Получение тренда дрейфа за последние N дней
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent_history = [
            h for h in self.drift_history
            if h['timestamp'] > cutoff
        ]
        
        if not recent_history:
            return {"error": "No drift history available"}
        
        drift_days = sum(1 for h in recent_history if h['drift_detected'])
        drift_ratio = drift_days / len(recent_history)
        
        # Анализ тренда (увеличивается ли дрейф)
        severity_values = {'high': 3, 'medium': 2, 'low': 1, 'none': 0}
        severity_scores = [severity_values.get(h['severity'], 0) for h in recent_history]
        
        if len(severity_scores) > 7:
            # Сравниваем первую и вторую половину
            half = len(severity_scores) // 2
            first_half_avg = np.mean(severity_scores[:half])
            second_half_avg = np.mean(severity_scores[half:])
            trend_increasing = second_half_avg > first_half_avg
        else:
            trend_increasing = False
        
        return {
            'period_days': days,
            'total_checks': len(recent_history),
            'drift_detected_count': drift_days,
            'drift_ratio': drift_ratio,
            'trend_increasing': trend_increasing,
            'current_severity': recent_history[-1]['severity'] if recent_history else 'none',
            'recommendation': (
                "Дрейф данных усиливается. Срочно переобучите модель!"
                if trend_increasing and drift_ratio > 0.3
                else "Дрейф стабилен. Продолжайте мониторинг"
            )
        }


# Глобальный экземпляр
drift_detector = DataDriftDetector()