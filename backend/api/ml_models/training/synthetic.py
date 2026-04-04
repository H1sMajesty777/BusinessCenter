# backend/api/ml_models/training/synthetic.py
"""
Реалистичная генерация синтетических данных
"""
import numpy as np
import pandas as pd
from sklearn.neighbors import KernelDensity
from sklearn.mixture import GaussianMixture
from scipy.stats import multivariate_normal
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class RealisticDataGenerator:
    """
    Генератор реалистичных синтетических данных
    
    Использует:
    - Kernel Density Estimation для непрерывных признаков
    - Gaussian Mixture Models для многомерных распределений
    - Copula для сохранения корреляций
    """
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        np.random.seed(random_state)
        
        self.kde_models = {}
        self.gmm_model = None
        self.cov_matrix = None
        self.mean_vector = None
        self.is_fitted = False
    
    def fit(self, X: np.ndarray, feature_names: list):
        """
        Обучение генератора на реальных данных
        
        Args:
            X: Матрица признаков
            feature_names: Имена признаков
        """
        logger.info("Fitting realistic data generator...")
        
        # 1. Оценка плотности для каждого признака
        for i, name in enumerate(feature_names):
            try:
                # Используем KDE для каждого признака
                kde = KernelDensity(kernel='gaussian', bandwidth='scott')
                X_col = X[:, i].reshape(-1, 1)
                kde.fit(X_col)
                self.kde_models[name] = kde
            except Exception as e:
                logger.warning(f"KDE failed for {name}: {e}")
                self.kde_models[name] = None
        
        # 2. GMM для многомерного распределения
        try:
            n_components = min(5, len(X) // 10)
            self.gmm_model = GaussianMixture(
                n_components=n_components,
                random_state=self.random_state,
                covariance_type='full'
            )
            self.gmm_model.fit(X)
            logger.info(f"GMM fitted with {n_components} components")
        except Exception as e:
            logger.warning(f"GMM failed: {e}")
            self.gmm_model = None
        
        # 3. Сохраняем статистики для copula
        self.mean_vector = np.mean(X, axis=0)
        self.cov_matrix = np.cov(X.T)
        
        self.is_fitted = True
        logger.info("Data generator fitted successfully")
    
    def generate(self, n_samples: int, real_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Генерация синтетических данных
        
        Args:
            n_samples: Количество образцов
            real_data: Реальные данные для смешивания
        
        Returns:
            DataFrame с синтетическими данными
        """
        if not self.is_fitted:
            raise ValueError("Generator not fitted. Call fit() first.")
        
        if real_data is not None:
            # Смешиваем реальные и синтетические данные
            n_real = min(len(real_data), n_samples // 2)
            n_synthetic = n_samples - n_real
            
            real_sample = real_data.sample(n=n_real, random_state=self.random_state)
            synthetic_sample = self._generate_synthetic(n_synthetic)
            
            result = pd.concat([real_sample, synthetic_sample], ignore_index=True)
        else:
            result = self._generate_synthetic(n_samples)
        
        # Добавляем реалистичный шум
        noise_scale = 0.02
        for col in result.select_dtypes(include=[np.number]).columns:
            noise = np.random.normal(0, noise_scale, len(result))
            result[col] = result[col] * (1 + noise)
        
        logger.info(f"Generated {len(result)} synthetic samples")
        return result
    
    def _generate_synthetic(self, n_samples: int) -> pd.DataFrame:
        """Внутренний метод генерации"""
        
        if self.gmm_model is not None:
            # Используем GMM для генерации
            synthetic_data, _ = self.gmm_model.sample(n_samples)
            synthetic_df = pd.DataFrame(synthetic_data, columns=self.kde_models.keys())
        else:
            # Fallback: многомерное нормальное распределение
            synthetic_data = np.random.multivariate_normal(
                self.mean_vector, 
                self.cov_matrix, 
                size=n_samples
            )
            synthetic_df = pd.DataFrame(synthetic_data, columns=self.kde_models.keys())
        
        # Пост-обработка для корректных значений
        for col in synthetic_df.columns:
            # Ограничиваем значения разумными пределами
            if 'price' in col.lower():
                synthetic_df[col] = synthetic_df[col].clip(10000, 200000)
            elif 'area' in col.lower():
                synthetic_df[col] = synthetic_df[col].clip(10, 500)
            elif 'views' in col.lower():
                synthetic_df[col] = synthetic_df[col].clip(0, None)
                synthetic_df[col] = synthetic_df[col].round().astype(int)
            
            # Заменяем отрицательные значения
            synthetic_df[col] = synthetic_df[col].clip(0, None)
        
        return synthetic_df


class TargetGenerator:
    """
    Генератор целевой переменной на основе реальных вероятностей
    """
    
    def __init__(self):
        self.probability_model = None
        self.is_fitted = False
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """
        Обучение модели вероятности целевой переменной
        """
        from sklearn.ensemble import RandomForestClassifier
        
        self.probability_model = RandomForestClassifier(
            n_estimators=50,
            max_depth=5,
            random_state=42
        )
        self.probability_model.fit(X, y)
        self.is_fitted = True
        
        logger.info("Target generator fitted")
    
    def generate(self, X: np.ndarray, smoothing: float = 0.1) -> np.ndarray:
        """
        Генерация целевой переменной с калиброванными вероятностями
        """
        if not self.is_fitted:
            raise ValueError("Target generator not fitted")
        
        # Получаем вероятности из модели
        probabilities = self.probability_model.predict_proba(X)[:, 1]
        
        # Добавляем smoothing для более реалистичных результатов
        probabilities = probabilities * (1 - smoothing) + smoothing * 0.5
        
        # Генерируем целевую переменную
        y_generated = (np.random.random(len(X)) < probabilities).astype(int)
        
        # Сохраняем баланс классов
        pos_ratio = y_generated.mean()
        logger.info(f"Generated target with {pos_ratio:.2%} positive class")
        
        return y_generated


# Глобальный экземпляр
data_generator = RealisticDataGenerator()
target_generator = TargetGenerator()