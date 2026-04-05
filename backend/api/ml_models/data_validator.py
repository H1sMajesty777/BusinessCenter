# backend/api/ml_models/data_validator.py
"""
Валидация данных для ML моделей
Проверка качества, полноты и корректности данных перед обучением
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
from collections import Counter
from decimal import Decimal

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Отчет о валидации данных"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    statistics: Dict[str, Any]
    recommendations: List[str]


def convert_decimal_to_float(df: pd.DataFrame) -> pd.DataFrame:
    """Конвертирует Decimal столбцы в float"""
    for col in df.columns:
        if df[col].dtype == 'object':
            # Проверяем, есть ли Decimal в колонке
            sample = df[col].dropna()
            if len(sample) > 0:
                first_val = sample.iloc[0]
                if isinstance(first_val, Decimal):
                    df[col] = df[col].apply(lambda x: float(x) if x is not None else x)
    return df


class DataValidator:
    """
    Валидатор данных для ML моделей
    """
    
    def __init__(self):
        self.required_columns = [
            'office_id', 'floor', 'area_sqm', 'price_per_month'
        ]
        
        self.column_ranges = {
            'floor': (1, 20),
            'area_sqm': (5, 1000),
            'price_per_month': (1000, 500000),
            'price_per_sqm': (100, 5000),
            'total_views': (0, 10000),
            'total_apps': (0, 1000),
            'total_contracts': (0, 100),
            'competition_ratio': (0, 1)
        }
        
        self.numeric_columns = [
            'floor', 'area_sqm', 'price_per_month', 'price_per_sqm',
            'total_views', 'total_apps', 'total_contracts', 'competition_ratio'
        ]
    
    def _convert_to_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """Конвертирует все колонки в числовые типы"""
        df = df.copy()
        
        # Конвертируем Decimal в float
        df = convert_decimal_to_float(df)
        
        # Принудительно конвертируем numeric колонки
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except Exception:
                pass
        
        return df
    
    def validate_features(self, df: pd.DataFrame, 
                          is_training: bool = True,
                          target_column: str = 'target') -> ValidationReport:
        """
        Валидация DataFrame с признаками
        """
        errors = []
        warnings = []
        statistics = {}
        
        # Конвертируем типы данных
        df = self._convert_to_numeric(df)
        
        # 1. Проверка на пустой DataFrame
        if df.empty:
            errors.append("DataFrame is empty")
            return ValidationReport(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                statistics={},
                recommendations=["Проверьте источник данных"]
            )
        
        # 2. Проверка обязательных колонок
        missing_cols = set(self.required_columns) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # 3. Проверка целевой переменной для обучения
        if is_training:
            if target_column not in df.columns:
                errors.append(f"Target column '{target_column}' not found")
            else:
                # Статистика целевой переменной
                target_values = df[target_column].dropna()
                if len(target_values) > 0:
                    target_stats = target_values.value_counts().to_dict()
                    statistics['target_distribution'] = {str(k): int(v) for k, v in target_stats.items()}
                    
                    pos_ratio = float(target_values.mean())
                    statistics['positive_ratio'] = pos_ratio
                    
                    if pos_ratio < 0.05:
                        warnings.append(f"Severe class imbalance: only {pos_ratio:.1%} positive samples")
                    elif pos_ratio < 0.1:
                        warnings.append(f"Class imbalance: {pos_ratio:.1%} positive samples")
        
        # 4. Проверка пропущенных значений
        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        if len(null_cols) > 0:
            for col, count in null_cols.items():
                null_ratio = count / len(df)
                if null_ratio > 0.5:
                    errors.append(f"Column '{col}' has {null_ratio:.1%} missing values")
                elif null_ratio > 0.1:
                    warnings.append(f"Column '{col}' has {null_ratio:.1%} missing values")
            
            statistics['null_counts'] = {str(k): int(v) for k, v in null_cols.to_dict().items()}
        
        # 5. Проверка диапазонов значений
        outliers = {}
        for col, (min_val, max_val) in self.column_ranges.items():
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    # Пробуем конвертировать в float
                    try:
                        col_data = col_data.astype(float)
                        out_of_range = col_data[(col_data < min_val) | (col_data > max_val)]
                        if len(out_of_range) > 0:
                            outliers[col] = {
                                'count': len(out_of_range),
                                'ratio': len(out_of_range) / len(col_data),
                                'min': float(out_of_range.min()),
                                'max': float(out_of_range.max())
                            }
                    except Exception:
                        pass
        
        if outliers:
            statistics['outliers'] = outliers
            warnings.append(f"Found outliers in {len(outliers)} columns")
        
        # 6. Статистика по числовым колонкам
        numeric_stats = {}
        for col in self.numeric_columns:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    try:
                        col_data = col_data.astype(float)
                        numeric_stats[col] = {
                            'mean': float(col_data.mean()),
                            'std': float(col_data.std()),
                            'min': float(col_data.min()),
                            'max': float(col_data.max()),
                            'q25': float(col_data.quantile(0.25)),
                            'q50': float(col_data.quantile(0.5)),
                            'q75': float(col_data.quantile(0.75))
                        }
                    except Exception as e:
                        logger.warning(f"Could not compute stats for {col}: {e}")
        
        statistics['numeric_stats'] = numeric_stats
        
        # 7. Проверка уникальности office_id
        if 'office_id' in df.columns:
            unique_count = df['office_id'].nunique()
            total_count = len(df)
            statistics['office_id_uniqueness'] = {
                'unique': int(unique_count),
                'total': int(total_count),
                'duplicates': int(total_count - unique_count)
            }
            
            if unique_count < total_count:
                warnings.append(f"Found {total_count - unique_count} duplicate office_ids")
        
        # 8. Проверка на константные колонки
        constant_cols = []
        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].std() == 0:
                constant_cols.append(col)
        
        if constant_cols:
            warnings.append(f"Constant columns detected: {constant_cols[:5]}")
            statistics['constant_columns'] = constant_cols
        
        # 9. Проверка размера данных
        if len(df) < 10 and is_training:
            errors.append(f"Insufficient data for training: only {len(df)} samples")
        elif len(df) < 50 and is_training:
            warnings.append(f"Small dataset for training: {len(df)} samples")
        
        statistics['dataset_size'] = len(df)
        statistics['feature_count'] = len([c for c in df.columns if c not in ['office_id', target_column]])
        
        # Генерация рекомендаций
        recommendations = []
        
        if len(errors) == 0:
            if is_training and statistics.get('positive_ratio', 1) < 0.1:
                recommendations.append("Используйте SMOTE или синтетические данные для балансировки классов")
            
            if len(df) < 100:
                recommendations.append("Рассмотрите использование синтетических данных для увеличения выборки")
            
            if outliers:
                recommendations.append("Проверьте выбросы - возможно, нужна их обработка")
        
        is_valid = len(errors) == 0
        
        # Логирование результатов
        if is_valid:
            logger.info(f"Data validation passed: {len(df)} samples, {statistics['feature_count']} features")
        else:
            logger.error(f"Data validation failed: {errors}")
        
        if warnings:
            logger.warning(f"Warnings: {len(warnings)}")
        
        return ValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            statistics=statistics,
            recommendations=recommendations
        )
    
    def validate_prediction_input(self, df: pd.DataFrame) -> ValidationReport:
        """Валидация входных данных для предсказания"""
        errors = []
        warnings = []
        statistics = {}
        
        # Конвертируем типы
        df = self._convert_to_numeric(df)
        
        # Проверка на пустой DataFrame
        if df.empty:
            errors.append("No data provided for prediction")
            return ValidationReport(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                statistics={},
                recommendations=["Проверьте office_id"]
            )
        
        # Проверка наличия office_id
        if 'office_id' not in df.columns:
            errors.append("Missing 'office_id' column for prediction")
        
        # Проверка, что все значения в допустимых пределах
        for col, (min_val, max_val) in self.column_ranges.items():
            if col in df.columns:
                try:
                    col_data = df[col].dropna().astype(float)
                    invalid = col_data[(col_data < min_val) | (col_data > max_val)]
                    if len(invalid) > 0:
                        warnings.append(f"Column '{col}' has {len(invalid)} out-of-range values")
                except Exception:
                    pass
        
        is_valid = len(errors) == 0
        
        return ValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            statistics=statistics,
            recommendations=["Убедитесь, что office_id существует в БД"] if is_valid else []
        )
    
    def detect_data_drift(self,
                         current_df: pd.DataFrame,
                         reference_df: pd.DataFrame,
                         feature_columns: List[str]) -> Dict[str, Any]:
        """Обнаружение дрейфа между текущими и референсными данными"""
        from scipy import stats
        
        # Конвертируем типы
        current_df = self._convert_to_numeric(current_df)
        reference_df = self._convert_to_numeric(reference_df)
        
        drift_results = {}
        drift_count = 0
        
        for col in feature_columns:
            if col in current_df.columns and col in reference_df.columns:
                try:
                    current_data = current_df[col].dropna().values
                    ref_data = reference_df[col].dropna().values
                    
                    # Конвертируем в float
                    current_data = current_data.astype(float)
                    ref_data = ref_data.astype(float)
                    
                    if len(current_data) > 0 and len(ref_data) > 0:
                        # KS-тест
                        ks_stat, p_value = stats.ks_2samp(current_data, ref_data)
                        
                        # Изменение среднего
                        mean_change = (current_data.mean() - ref_data.mean()) / (ref_data.std() + 1e-8)
                        
                        drift_detected = p_value < 0.05
                        if drift_detected:
                            drift_count += 1
                        
                        drift_results[col] = {
                            'drift_detected': drift_detected,
                            'ks_pvalue': float(p_value),
                            'mean_change_std': float(mean_change),
                            'ref_mean': float(ref_data.mean()),
                            'current_mean': float(current_data.mean())
                        }
                except Exception as e:
                    logger.warning(f"Could not detect drift for {col}: {e}")
        
        drift_ratio = drift_count / len(feature_columns) if feature_columns else 0
        
        return {
            'drift_detected': drift_ratio > 0.3,
            'drift_ratio': drift_ratio,
            'affected_features_count': drift_count,
            'total_features': len(feature_columns),
            'features': drift_results,
            'recommendation': "Рекомендуется переобучение модели" if drift_ratio > 0.3 else "Дрейф не критичен"
        }


# Глобальный экземпляр
data_validator = DataValidator()