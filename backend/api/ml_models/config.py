# backend/api/ml_models/config.py
"""
Конфигурация ML модуля
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class MLConfig:
    """Конфигурация ML моделей"""
    
    # Пути
    MODEL_DIR: Path = Path(os.getenv('ML_MODEL_DIR', '/app/data/models'))
    CACHE_DIR: Path = Path(os.getenv('ML_CACHE_DIR', '/app/data/cache'))
    LOG_DIR: Path = Path(os.getenv('ML_LOG_DIR', '/app/logs/ml'))
    
    # Параметры обучения
    TEST_SIZE: float = 0.2
    VALIDATION_SIZE: float = 0.2
    RANDOM_STATE: int = 42
    CV_FOLDS: int = 5
    
    # Параметры моделей
    ENSEMBLE_MODELS: list = None  # Установим в __post_init__
    NEURAL_EPOCHS: int = 100
    EARLY_STOPPING_PATIENCE: int = 20
    
    # Кэширование
    CACHE_TTL_SECONDS: int = 3600  # 1 час
    MAX_CACHE_SIZE: int = 1000
    
    # Мониторинг
    DRIFT_WINDOW_DAYS: int = 30
    ALERT_THRESHOLD_AUC_DROP: float = 0.1
    
    def __post_init__(self):
        if self.ENSEMBLE_MODELS is None:
            self.ENSEMBLE_MODELS = ['randomforest', 'xgboost', 'lightgbm']
        
        # Создаём директории
        for dir_path in [self.MODEL_DIR, self.CACHE_DIR, self.LOG_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @property
    def model_metadata_path(self) -> Path:
        return self.MODEL_DIR / 'metadata.json'
    
    @property
    def model_weights_path(self) -> Path:
        return self.MODEL_DIR / 'model_weights.pkl'
    
    @property
    def scaler_path(self) -> Path:
        return self.MODEL_DIR / 'scaler.pkl'


# Глобальный конфиг
config = MLConfig()