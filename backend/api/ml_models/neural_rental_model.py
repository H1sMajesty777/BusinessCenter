#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Мощная нейросетевая модель для предсказания аренды офисов
Использует: PyTorch, XGBoost, CatBoost, LightGBM
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import xgboost as xgb
import catboost as ctb
import lightgbm as lgb
import joblib
from typing import Dict, Any, List
import warnings
warnings.filterwarnings('ignore')

# Устройство для PyTorch
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

class RentalNeuralNetwork(nn.Module):
    """Глубокая нейронная сеть для предсказания аренды"""
    
    def __init__(self, input_dim, hidden_dims=[128, 256, 128, 64]):
        super(RentalNeuralNetwork, self).__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.3))
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, 32))
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(0.2))
        layers.append(nn.Linear(32, 1))
        layers.append(nn.Sigmoid())
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


class AdvancedRentalPredictor:
    """Продвинутый предиктор с ансамблем моделей"""
    
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = None
        
    def extract_features(self, conn, office_ids=None) -> pd.DataFrame:
        """Извлечение расширенных признаков"""
        cursor = conn.cursor()
        
        # Базовый запрос для офисов
        if office_ids:
            query = f"""
                SELECT o.id, o.office_number, o.floor, o.area_sqm, o.price_per_month,
                       o.is_free, o.created_at
                FROM offices o
                WHERE o.id IN ({','.join(map(str, office_ids))})
            """
        else:
            query = """
                SELECT o.id, o.office_number, o.floor, o.area_sqm, o.price_per_month,
                       o.is_free, o.created_at
                FROM offices o
            """
        
        cursor.execute(query)
        offices = cursor.fetchall()
        
        features = []
        
        for office in offices:
            office_id = office[0]
            
            # 1. Статистика просмотров
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_views,
                    COUNT(DISTINCT user_id) as unique_viewers,
                    AVG(duration_seconds) as avg_duration,
                    SUM(CASE WHEN is_contacted THEN 1 ELSE 0 END) as total_contacts,
                    COUNT(CASE WHEN viewed_at > NOW() - INTERVAL '7 days' THEN 1 END) as views_7d,
                    COUNT(CASE WHEN viewed_at > NOW() - INTERVAL '30 days' THEN 1 END) as views_30d,
                    COUNT(CASE WHEN viewed_at > NOW() - INTERVAL '90 days' THEN 1 END) as views_90d
                FROM office_views 
                WHERE office_id = %s
            """, (office_id,))
            views_stats = cursor.fetchone()
            
            # 2. Статистика заявок
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_apps,
                    COUNT(CASE WHEN status_id = 2 THEN 1 END) as approved_apps,
                    COUNT(CASE WHEN status_id = 3 THEN 1 END) as rejected_apps,
                    AVG(EXTRACT(DAY FROM (NOW() - created_at))) as days_since_last_app
                FROM applications 
                WHERE office_id = %s
            """, (office_id,))
            apps_stats = cursor.fetchone()
            
            # 3. История аренды
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_contracts,
                    AVG(total_amount) as avg_contract_amount,
                    AVG(EXTRACT(DAY FROM (end_date - start_date))) as avg_duration_days,
                    COUNT(CASE WHEN status_id = 4 THEN 1 END) as active_contracts
                FROM contracts 
                WHERE office_id = %s
            """, (office_id,))
            contract_stats = cursor.fetchone()
            
            # 4. Конкуренция на этаже
            floor = office[2]
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_on_floor,
                    SUM(CASE WHEN is_free THEN 1 ELSE 0 END) as free_on_floor,
                    AVG(price_per_month) as avg_price_on_floor
                FROM offices 
                WHERE floor = %s
            """, (floor,))
            competition = cursor.fetchone()
            
            # Формируем признаки
            price = float(office[4])
            area = float(office[3])
            price_per_sqm = price / area if area > 0 else 0
            
            features.append({
                'office_id': office_id,
                'floor': floor,
                'area_sqm': area,
                'price_per_month': price,
                'price_per_sqm': price_per_sqm,
                'is_free': 1 if office[5] else 0,
                'total_views': views_stats[0] or 0,
                'unique_viewers': views_stats[1] or 0,
                'avg_view_duration': views_stats[2] or 0,
                'contact_rate': (views_stats[3] / views_stats[0] if views_stats[0] > 0 else 0),
                'views_7d': views_stats[4] or 0,
                'views_30d': views_stats[5] or 0,
                'views_90d': views_stats[6] or 0,
                'total_apps': apps_stats[0] or 0,
                'approval_rate': (apps_stats[1] / apps_stats[0] if apps_stats[0] > 0 else 0),
                'days_since_last_app': apps_stats[3] or 90,
                'total_contracts': contract_stats[0] or 0,
                'avg_contract_amount': contract_stats[1] or 0,
                'avg_contract_duration': contract_stats[2] or 0,
                'active_contracts': contract_stats[3] or 0,
                'competition_ratio': (competition[1] / competition[0] if competition[0] > 0 else 1),
                'avg_price_on_floor': competition[2] or price,
                'price_competition_ratio': price / (competition[2] or price) if competition[2] else 1
            })
        
        cursor.close()
        return pd.DataFrame(features)
    
    def train_neural_network(self, X_train, y_train, X_val, y_val, epochs=100):
        """Обучение нейронной сети"""
        print("🧠 Обучение нейронной сети...")
        
        # Конвертируем в тензоры
        X_train_t = torch.FloatTensor(X_train).to(device)
        y_train_t = torch.FloatTensor(y_train).to(device)
        X_val_t = torch.FloatTensor(X_val).to(device)
        y_val_t = torch.FloatTensor(y_val).to(device)
        
        # Даталоадеры
        train_dataset = TensorDataset(X_train_t, y_train_t)
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        
        # Модель
        model = RentalNeuralNetwork(X_train.shape[1]).to(device)
        criterion = nn.BCELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
        
        # Обучение
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(epochs):
            model.train()
            train_loss = 0
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = model(batch_X).squeeze()
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()
            
            # Валидация
            model.eval()
            with torch.no_grad():
                val_outputs = model(X_val_t).squeeze()
                val_loss = criterion(val_outputs, y_val_t).item()
                val_auc = roc_auc_score(y_val, val_outputs.cpu().numpy())
            
            scheduler.step(val_loss)
            
            if (epoch + 1) % 20 == 0:
                print(f"   Epoch {epoch+1}/{epochs} - Train Loss: {train_loss/len(train_loader):.4f}, Val Loss: {val_loss:.4f}, Val AUC: {val_auc:.4f}")
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                torch.save(model.state_dict(), '/app/api/ml_models/best_nn_model.pt')
            else:
                patience_counter += 1
                if patience_counter >= 20:
                    print(f"   Early stopping at epoch {epoch+1}")
                    break
        
        return model
    
    def train(self, conn):
        """Обучение ансамбля моделей"""
        print("\n" + "="*60)
        print("🚀 ОБУЧЕНИЕ ПРОДВИНУТОЙ ML МОДЕЛИ")
        print("="*60 + "\n")
        
        # Извлекаем признаки
        df = self.extract_features(conn)
        
        if len(df) < 10:
            print("❌ Недостаточно данных для обучения")
            return {"status": "error", "message": "Need at least 10 samples"}
        
        # Целевая переменная: была ли аренда за последние 3 месяца
        cursor = conn.cursor()
        target = []
        for office_id in df['office_id']:
            cursor.execute("""
                SELECT COUNT(*) FROM contracts 
                WHERE office_id = %s AND signed_at > NOW() - INTERVAL '3 months'
            """, (int(office_id),))
            count = cursor.fetchone()[0]
            target.append(1 if count > 0 else 0)
        cursor.close()
        
        df['target'] = target
        
        # Подготовка признаков
        feature_cols = [col for col in df.columns if col not in ['office_id', 'target']]
        self.feature_columns = feature_cols
        
        X = df[feature_cols].values
        y = df['target'].values
        
        # Нормализация
        X_scaled = self.scaler.fit_transform(X)
        
        # Разделение
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Обучаем нейросеть
        X_train_nn, X_val, y_train_nn, y_val = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42
        )
        nn_model = self.train_neural_network(X_train_nn, y_train_nn, X_val, y_val)
        
        # Обучаем XGBoost
        print("\n🌲 Обучение XGBoost...")
        xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        xgb_model.fit(X_train, y_train)
        
        # Обучаем CatBoost
        print("🐱 Обучение CatBoost...")
        cat_model = ctb.CatBoostClassifier(
            iterations=200,
            depth=6,
            learning_rate=0.05,
            random_seed=42,
            verbose=False
        )
        cat_model.fit(X_train, y_train)
        
        # Обучаем LightGBM
        print("💡 Обучение LightGBM...")
        lgb_model = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1
        )
        lgb_model.fit(X_train, y_train)
        
        # Обучаем RandomForest
        print("🌳 Обучение RandomForest...")
        rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        rf_model.fit(X_train, y_train)
        
        # Сохраняем модели
        self.models = {
            'neural_network': nn_model,
            'xgboost': xgb_model,
            'catboost': cat_model,
            'lightgbm': lgb_model,
            'randomforest': rf_model
        }
        
        # Оценка качества
        print("\n📊 ОЦЕНКА КАЧЕСТВА МОДЕЛЕЙ:")
        results = {}
        
        for name, model in self.models.items():
            if name == 'neural_network':
                model.eval()
                with torch.no_grad():
                    X_test_t = torch.FloatTensor(X_test).to(device)
                    pred_proba = model(X_test_t).squeeze().cpu().numpy()
            else:
                pred_proba = model.predict_proba(X_test)[:, 1]
            
            pred = (pred_proba > 0.5).astype(int)
            auc = roc_auc_score(y_test, pred_proba)
            acc = accuracy_score(y_test, pred)
            results[name] = {'accuracy': acc, 'roc_auc': auc}
            print(f"   {name.upper()}: AUC = {auc:.4f}, Accuracy = {acc:.4f}")
        
        # Ансамбль (усреднение вероятностей)
        self.is_trained = True
        
        # Сохраняем всё
        joblib.dump(self, '/app/api/ml_models/advanced_rental_predictor.pkl')
        joblib.dump(self.scaler, '/app/api/ml_models/advanced_scaler.pkl')
        
        print("\n✅ Модели успешно обучены и сохранены!")
        
        return {
            "status": "trained",
            "models_count": len(self.models),
            "feature_count": len(feature_cols),
            "results": results,
            "samples_used": len(df)
        }
    
    def predict(self, conn, office_id: int) -> Dict[str, Any]:
        """Предсказание вероятности аренды"""
        if not self.is_trained:
            return {"error": "Model not trained yet"}
        
        df = self.extract_features(conn, [office_id])
        if len(df) == 0:
            return {"error": f"Office {office_id} not found"}
        
        X = df[self.feature_columns].values
        X_scaled = self.scaler.transform(X)
        X_tensor = torch.FloatTensor(X_scaled).to(device)
        
        # Получаем предсказания от всех моделей
        predictions = []
        
        # Нейросеть
        with torch.no_grad():
            nn_pred = self.models['neural_network'](X_tensor).squeeze().cpu().numpy()[0]
        predictions.append(nn_pred)
        
        # XGBoost
        xgb_pred = self.models['xgboost'].predict_proba(X_scaled)[0, 1]
        predictions.append(xgb_pred)
        
        # CatBoost
        cat_pred = self.models['catboost'].predict_proba(X_scaled)[0, 1]
        predictions.append(cat_pred)
        
        # LightGBM
        lgb_pred = self.models['lightgbm'].predict_proba(X_scaled)[0, 1]
        predictions.append(lgb_pred)
        
        # RandomForest
        rf_pred = self.models['randomforest'].predict_proba(X_scaled)[0, 1]
        predictions.append(rf_pred)
        
        # Ансамбль
        probability = np.mean(predictions)
        
        # Категория
        if probability >= 0.7:
            category = "high"
            description = "🔥 Высокая вероятность аренды! Офис востребован."
        elif probability >= 0.4:
            category = "medium"
            description = "📊 Средняя вероятность аренды. Есть потенциал."
        else:
            category = "low"
            description = "⚠️ Низкая вероятность аренды. Требуется анализ."
        
        return {
            "office_id": office_id,
            "probability": float(probability),
            "probability_percent": round(probability * 100, 1),
            "category": category,
            "description": description,
            "model_predictions": {
                "neural_network": float(nn_pred),
                "xgboost": float(xgb_pred),
                "catboost": float(cat_pred),
                "lightgbm": float(lgb_pred),
                "randomforest": float(rf_pred)
            },
            "ensemble_size": len(predictions)
        }


# Глобальный экземпляр
advanced_predictor = AdvancedRentalPredictor()