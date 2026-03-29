from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from api.database import get_db
from api.security import decode_token

router = APIRouter()

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Нет токена")
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    return payload

def require_admin_or_manager(current_user: dict):
    if current_user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Только админ и менеджер")

@router.post("/api/ai/train", tags=["AI"])
def train_model(current_user: dict = Depends(get_current_user)):
    """Обучение ML модели — ТОЛЬКО АДМИН"""
    from api.ai.occupancy_predictor import predictor
    
    if current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Только администраторы")
    
    r2_score = predictor.train()
    
    return {"message": "ML модель обучена", "model_type": "RandomForestRegressor", "r2_score": r2_score, "status": "success"}

@router.get("/api/ai/offices/predict", tags=["AI"])
def predict_all_offices(current_user: dict = Depends(get_current_user)):
    """
    Просмотр прогнозов ИИ
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    from api.ai.occupancy_predictor import predictor
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, office_number, area_sqm, floor, price_per_month FROM offices ORDER BY id")
    offices = cursor.fetchall()
    cursor.close()
    conn.close()
    
    results = []
    for office in offices:
        office_data = {'id': office[0], 'office_number': office[1], 'area_sqm': office[2], 'floor': office[3], 'price_per_month': office[4]}
        prediction = predictor.predict_for_office(office_data)
        results.append(prediction)
    
    avg_occupancy = round(sum(r['predicted_occupancy'] for r in results) / len(results), 1) if results else 0
    
    return {"total_offices": len(results), "average_occupancy": avg_occupancy, "offices": results}

@router.get("/api/ai/status", tags=["AI"])
def get_ai_status():
    """Статус ML модели — Все"""
    from api.ai.occupancy_predictor import predictor
    
    return {"model_trained": predictor.is_trained, "model_type": "RandomForestRegressor", "features": ["area_sqm", "floor", "price_per_sqm", "month"]}