# backend/api/ml_models/models/neural.py
"""
Нейросетевая модель для предсказания аренды офисов
С поддержкой GPU, ранней остановкой и регуляризацией
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
from torch.optim.lr_scheduler import ReduceLROnPlateau, CosineAnnealingWarmRestarts
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Определяем устройство
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
logger.info(f"Using device: {device}")


@dataclass
class NeuralNetworkConfig:
    """Конфигурация нейросети"""
    input_dim: int
    hidden_dims: List[int] = None
    dropout_rate: float = 0.3
    batch_norm: bool = True
    activation: str = 'relu'
    learning_rate: float = 0.001
    weight_decay: float = 1e-5
    epochs: int = 100
    batch_size: int = 32
    early_stopping_patience: int = 20
    use_scheduler: bool = True
    
    def __post_init__(self):
        if self.hidden_dims is None:
            self.hidden_dims = [256, 128, 64, 32]


class ResidualBlock(nn.Module):
    """Residual блок для улучшения обучения глубоких сетей"""
    
    def __init__(self, dim: int, dropout: float = 0.3):
        super().__init__()
        self.linear1 = nn.Linear(dim, dim)
        self.bn1 = nn.BatchNorm1d(dim)
        self.linear2 = nn.Linear(dim, dim)
        self.bn2 = nn.BatchNorm1d(dim)
        self.dropout = nn.Dropout(dropout)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        residual = x
        out = self.relu(self.bn1(self.linear1(x)))
        out = self.dropout(out)
        out = self.bn2(self.linear2(out))
        out = self.dropout(out)
        out = out + residual
        return self.relu(out)


class AdvancedRentalNeuralNetwork(nn.Module):
    """
    Продвинутая нейросеть для предсказания аренды
    
    Архитектура:
    - Входной слой с BatchNorm
    - Несколько Residual блоков
    - Dropout для регуляризации
    - Выходной слой с Sigmoid
    """
    
    def __init__(self, config: NeuralNetworkConfig):
        super().__init__()
        
        self.config = config
        layers = []
        
        # Входной слой с нормализацией
        layers.append(nn.Linear(config.input_dim, config.hidden_dims[0]))
        if config.batch_norm:
            layers.append(nn.BatchNorm1d(config.hidden_dims[0]))
        layers.append(self._get_activation(config.activation))
        layers.append(nn.Dropout(config.dropout_rate))
        
        # Скрытые слои с Residual блоками
        prev_dim = config.hidden_dims[0]
        for hidden_dim in config.hidden_dims[1:]:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            if config.batch_norm:
                layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(self._get_activation(config.activation))
            layers.append(nn.Dropout(config.dropout_rate))
            prev_dim = hidden_dim
        
        # Residual блоки для лучшего обучения
        self.res_blocks = nn.ModuleList([
            ResidualBlock(config.hidden_dims[-1], config.dropout_rate)
            for _ in range(3)
        ])
        
        # Выходной слой
        layers.append(nn.Linear(config.hidden_dims[-1], 32))
        layers.append(self._get_activation(config.activation))
        layers.append(nn.Dropout(config.dropout_rate / 2))
        layers.append(nn.Linear(32, 1))
        layers.append(nn.Sigmoid())
        
        self.network = nn.Sequential(*layers)
        
        # Инициализация весов
        self._initialize_weights()
    
    def _get_activation(self, name: str) -> nn.Module:
        """Получение функции активации"""
        activations = {
            'relu': nn.ReLU(),
            'leaky_relu': nn.LeakyReLU(0.1),
            'elu': nn.ELU(),
            'gelu': nn.GELU()
        }
        return activations.get(name, nn.ReLU())
    
    def _initialize_weights(self):
        """Инициализация весов Xavier/Glorot"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        out = self.network(x)
        
        # Применяем residual блоки
        for res_block in self.res_blocks:
            out = res_block(out)
        
        return out


class NeuralRentalPredictor:
    """
    Обучатель и предиктор на основе нейросети
    
    Особенности:
    - Автоматическое определение GPU/CPU
    - Ранняя остановка
    - Learning rate scheduling
    - Weighted sampling для несбалансированных данных
    - Сохранение лучших весов
    """
    
    def __init__(self, model_dir: str = "/app/data/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.config = None
        self.is_trained = False
        self.best_val_loss = float('inf')
        self.training_history = []
    
    def _prepare_dataloaders(self, 
                            X_train: np.ndarray, 
                            y_train: np.ndarray,
                            X_val: np.ndarray,
                            y_val: np.ndarray,
                            batch_size: int = 32) -> Tuple[DataLoader, DataLoader]:
        """
        Подготовка DataLoader'ов с балансировкой весов
        """
        # Конвертируем в тензоры
        X_train_t = torch.FloatTensor(X_train).to(device)
        y_train_t = torch.FloatTensor(y_train).to(device)
        X_val_t = torch.FloatTensor(X_val).to(device)
        y_val_t = torch.FloatTensor(y_val).to(device)
        
        # Веса для несбалансированных классов
        class_counts = np.bincount(y_train.astype(int))
        if len(class_counts) > 1 and class_counts[0] > 0 and class_counts[1] > 0:
            class_weights = 1.0 / class_counts
            sample_weights = np.array([class_weights[int(y)] for y in y_train])
            sample_weights = torch.FloatTensor(sample_weights)
            
            sampler = WeightedRandomSampler(
                weights=sample_weights,
                num_samples=len(sample_weights),
                replacement=True
            )
            train_dataset = TensorDataset(X_train_t, y_train_t)
            train_loader = DataLoader(
                train_dataset, 
                batch_size=batch_size, 
                sampler=sampler
            )
        else:
            train_dataset = TensorDataset(X_train_t, y_train_t)
            train_loader = DataLoader(
                train_dataset, 
                batch_size=batch_size, 
                shuffle=True
            )
        
        val_dataset = TensorDataset(X_val_t, y_val_t)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        return train_loader, val_loader
    
    def train(self, 
              X_train: np.ndarray, 
              y_train: np.ndarray,
              X_val: np.ndarray,
              y_val: np.ndarray,
              config: Optional[NeuralNetworkConfig] = None) -> Dict[str, Any]:
        """
        Обучение нейросети
        
        Args:
            X_train: Обучающие признаки
            y_train: Обучающие целевые значения
            X_val: Валидационные признаки
            y_val: Валидационные целевые значения
            config: Конфигурация сети
        
        Returns:
            Dict с историей обучения и метриками
        """
        if config is None:
            config = NeuralNetworkConfig(input_dim=X_train.shape[1])
        
        self.config = config
        
        logger.info(f"Training neural network on {device}")
        logger.info(f"Input dimension: {config.input_dim}")
        logger.info(f"Hidden layers: {config.hidden_dims}")
        logger.info(f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}")
        
        # Создаем модель
        self.model = AdvancedRentalNeuralNetwork(config).to(device)
        
        # Функция потерь (BCEWithLogitsLoss более стабильна)
        criterion = nn.BCELoss()
        
        # Оптимизатор с AdamW (лучше чем Adam)
        optimizer = optim.AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )
        
        # Learning rate scheduler
        if config.use_scheduler:
            scheduler = ReduceLROnPlateau(
                optimizer, 
                mode='min', 
                factor=0.5, 
                patience=10,
                verbose=True
            )
        else:
            scheduler = None
        
        # Подготовка DataLoader'ов
        train_loader, val_loader = self._prepare_dataloaders(
            X_train, y_train, X_val, y_val, config.batch_size
        )
        
        # Обучение
        best_model_state = None
        patience_counter = 0
        history = {'train_loss': [], 'val_loss': [], 'val_auc': []}
        
        for epoch in range(config.epochs):
            # Training
            self.model.train()
            train_loss = 0.0
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = self.model(batch_X).squeeze()
                loss = criterion(outputs, batch_y)
                loss.backward()
                
                # Gradient clipping для стабильности
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                
                optimizer.step()
                train_loss += loss.item()
            
            avg_train_loss = train_loss / len(train_loader)
            
            # Validation
            self.model.eval()
            val_loss = 0.0
            val_preds = []
            val_targets = []
            
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    outputs = self.model(batch_X).squeeze()
                    loss = criterion(outputs, batch_y)
                    val_loss += loss.item()
                    
                    val_preds.extend(outputs.cpu().numpy())
                    val_targets.extend(batch_y.cpu().numpy())
            
            avg_val_loss = val_loss / len(val_loader)
            
            # Вычисляем AUC
            from sklearn.metrics import roc_auc_score
            val_auc = roc_auc_score(val_targets, val_preds)
            
            # Сохраняем историю
            history['train_loss'].append(avg_train_loss)
            history['val_loss'].append(avg_val_loss)
            history['val_auc'].append(val_auc)
            
            # Логирование
            if (epoch + 1) % 10 == 0:
                logger.info(
                    f"Epoch {epoch+1}/{config.epochs} - "
                    f"Train Loss: {avg_train_loss:.4f}, "
                    f"Val Loss: {avg_val_loss:.4f}, "
                    f"Val AUC: {val_auc:.4f}"
                )
            
            # Learning rate scheduling
            if scheduler:
                scheduler.step(avg_val_loss)
            
            # Early stopping
            if avg_val_loss < self.best_val_loss:
                self.best_val_loss = avg_val_loss
                best_model_state = self.model.state_dict().copy()
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= config.early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break
        
        # Загружаем лучшую модель
        if best_model_state:
            self.model.load_state_dict(best_model_state)
        
        self.is_trained = True
        self.training_history = history
        
        # Сохраняем модель
        self._save_model()
        
        # Финальная оценка
        final_val_auc = max(history['val_auc']) if history['val_auc'] else 0
        
        return {
            'status': 'trained',
            'epochs_completed': len(history['train_loss']),
            'best_val_loss': float(self.best_val_loss),
            'best_val_auc': float(final_val_auc),
            'history': history,
            'config': {
                'input_dim': config.input_dim,
                'hidden_dims': config.hidden_dims,
                'dropout_rate': config.dropout_rate,
                'learning_rate': config.learning_rate
            }
        }
    
    def _save_model(self):
        """Сохранение модели и конфигурации"""
        if self.model is None:
            return
        
        model_path = self.model_dir / 'neural_model.pt'
        config_path = self.model_dir / 'neural_config.json'
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'config': {
                'input_dim': self.config.input_dim,
                'hidden_dims': self.config.hidden_dims,
                'dropout_rate': self.config.dropout_rate,
                'batch_norm': self.config.batch_norm,
                'activation': self.config.activation
            },
            'training_history': self.training_history,
            'best_val_loss': self.best_val_loss
        }, model_path)
        
        logger.info(f"Neural network saved to {model_path}")
    
    def load_model(self, model_path: Optional[Path] = None):
        """Загрузка сохранённой модели"""
        if model_path is None:
            model_path = self.model_dir / 'neural_model.pt'
        
        if not model_path.exists():
            logger.warning(f"Model not found at {model_path}")
            return False
        
        try:
            checkpoint = torch.load(model_path, map_location=device)
            
            # Восстанавливаем конфиг
            config = NeuralNetworkConfig(
                input_dim=checkpoint['config']['input_dim'],
                hidden_dims=checkpoint['config']['hidden_dims'],
                dropout_rate=checkpoint['config']['dropout_rate'],
                batch_norm=checkpoint['config']['batch_norm'],
                activation=checkpoint['config']['activation']
            )
            
            self.config = config
            self.model = AdvancedRentalNeuralNetwork(config).to(device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.training_history = checkpoint.get('training_history', [])
            self.best_val_loss = checkpoint.get('best_val_loss', float('inf'))
            self.is_trained = True
            
            logger.info(f"Neural network loaded from {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Предсказание вероятностей
        
        Args:
            X: Признаки для предсказания
        
        Returns:
            np.ndarray с вероятностями
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained or loaded")
        
        self.model.eval()
        X_tensor = torch.FloatTensor(X).to(device)
        
        with torch.no_grad():
            predictions = self.model(X_tensor).squeeze().cpu().numpy()
        
        return predictions
    
    def get_model_info(self) -> Dict[str, Any]:
        """Информация о модели"""
        return {
            'is_trained': self.is_trained,
            'device': str(device),
            'config': {
                'input_dim': self.config.input_dim if self.config else None,
                'hidden_dims': self.config.hidden_dims if self.config else None,
                'dropout_rate': self.config.dropout_rate if self.config else None
            } if self.config else {},
            'best_val_loss': float(self.best_val_loss) if self.best_val_loss != float('inf') else None,
            'epochs_trained': len(self.training_history) if self.training_history else 0
        }


# Глобальный экземпляр
neural_predictor = NeuralRentalPredictor()