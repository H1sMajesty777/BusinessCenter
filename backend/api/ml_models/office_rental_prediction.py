# -*- coding: utf-8 -*-
"""Office Rental Prediction - ЗАГЛУШКА (без sklearn/pandas)"""

class OfficeRentalPredictor:
    """Заглушка для демонстрации без внешних зависимостей"""
    
    def __init__(self):
        self.is_trained = False
    
    def train(self, conn):
        self.is_trained = True
        return {
            "status": "stub",
            "message": "Заглушка активна",
            "samples_used": 0
        }
    
    def predict_probability(self, conn, office_id: int):
        """Заглушка прогноза — на основе просмотров"""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM office_views WHERE office_id = %s", (office_id,))
        views = cursor.fetchone()[0]
        cursor.close()
        
        if views >= 10:
            category, prob = 'high', 0.85
        elif views >= 5:
            category, prob = 'medium', 0.55
        else:
            category, prob = 'low', 0.25
        
        return {
            "office_id": office_id,
            "probability": prob,
            "probability_percent": prob * 100,
            "category": category,
            "description": {
                'high': 'Высокая вероятность аренды в этом месяце',
                'medium': 'Средняя вероятность аренды в этом месяце',
                'low': 'Низкая вероятность аренды в этом месяце'
            }[category],
            "top_factors": [
                {"feature": "view_count", "importance": 0.4},
                {"feature": "application_count", "importance": 0.35},
                {"feature": "contact_rate", "importance": 0.25}
            ]
        }
    
    def predict_batch(self, conn, office_ids):
        return [self.predict_probability(conn, oid) for oid in office_ids]

rental_predictor = OfficeRentalPredictor()
