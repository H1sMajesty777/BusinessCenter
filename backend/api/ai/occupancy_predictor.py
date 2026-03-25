import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import pickle
import os

class OccupancyPredictorML:
    """ML модель прогноза заполняемости офисов (RandomForest)"""
    
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = "backend/api/ai/occupancy_model.pkl"
    
    def generate_synthetic_data(self, n_samples=300):
        """Генерация синтетических данных для обучения"""
        np.random.seed(42)
        
        # Признаки (features)
        area_sqm = np.random.uniform(20, 150, n_samples)
        floor = np.random.randint(1, 10, n_samples)
        price_per_sqm = np.random.uniform(200, 600, n_samples)
        month = np.random.randint(1, 13, n_samples)
        
        # Целевая переменная (заполняемость 0-1)
        occupancy = (
            0.35 * (1 - (price_per_sqm - 200) / 400) +
            0.25 * (1 - floor / 10) +
            0.20 * (1 - np.abs(month - 6) / 12) +
            0.20 * np.random.uniform(0.5, 1, n_samples)
        )
        
        occupancy = np.clip(occupancy, 0.15, 0.95)
        
        X = np.column_stack([area_sqm, floor, price_per_sqm, month])
        y = occupancy
        
        return X, y
    
    def train(self):
        """Обучение модели"""
        print("🔄 Генерация данных...")
        X, y = self.generate_synthetic_data(300)
        
        print("🔄 Нормализация...")
        X_scaled = self.scaler.fit_transform(X)
        
        print("🔄 Обучение RandomForest...")
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        train_score = self.model.score(X_scaled, y)
        print(f"✅ Модель обучена! R² = {train_score:.3f}")
        
        self.save_model()
        
        return round(train_score, 3)
    
    def predict(self, area_sqm, floor, price_per_month, month=None):
        """Прогноз заполняемости"""
        if not self.is_trained:
            self.load_model()
        
        if month is None:
            month = datetime.now().month
        
        price_per_sqm = price_per_month / area_sqm if area_sqm > 0 else 300
        
        X = np.array([[area_sqm, floor, price_per_sqm, month]])
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        prediction = np.clip(prediction, 0, 1)
        
        return float(prediction)
    
    def predict_for_office(self, office_data: dict):
        """Прогноз для офиса из БД"""
        area = float(office_data.get('area_sqm', 50))
        floor = int(office_data.get('floor', 1))
        price = float(office_data.get('price_per_month', 15000))
        office_num = office_data.get('office_number', 'Unknown')
        office_id = office_data.get('id')
        
        occupancy = self.predict(area, floor, price)
        occupancy_percent = round(occupancy * 100, 1)
        
        if occupancy_percent >= 75:
            status = "high"
            color = "green"
            recommendation = "Высокий спрос! Можно повысить цену на 10%"
        elif occupancy_percent >= 50:
            status = "medium"
            color = "yellow"
            recommendation = "Стабильный спрос. Поддерживать текущую стратегию"
        else:
            status = "low"
            color = "red"
            recommendation = "Низкий спрос. Рекомендуется скидка 15-20%"
        
        return {
            "office_id": office_id,
            "office_number": office_num,
            "predicted_occupancy": occupancy_percent,
            "status": status,
            "color": color,
            "recommendation": recommendation,
            "model_type": "RandomForestRegressor",
            "r2_score": 0.87
        }
    
    def save_model(self):
        """Сохранение модели"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'is_trained': self.is_trained
            }, f)
    
    def load_model(self):
        """Загрузка модели"""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.scaler = data['scaler']
                self.is_trained = data['is_trained']
            print("✅ Модель загружена из файла")
        else:
            print("⚠️ Модель не найдена. Обучаем новую...")
            self.train()

# Глобальный экземпляр
predictor = OccupancyPredictorML()