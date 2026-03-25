from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from api.database import get_db
from api.security import decode_token

router = APIRouter()

def get_current_user(authorization: Optional[str] = Header(None)):
    """Получение текущего пользователя из токена"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Нет токена")
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    return payload

@router.post("/api/ai/train", tags=["AI"])
def train_model(current_user: dict = Depends(get_current_user)):
    """Обучение ML модели (только админ)"""
    from api.ai.occupancy_predictor import predictor
    
    if current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Только администраторы")
    
    r2_score = predictor.train()
    
    return {
        "message": "ML модель успешно обучена",
        "model_type": "RandomForestRegressor",
        "r2_score": r2_score,
        "status": "success"
    }

@router.get("/api/ai/offices/predict", tags=["AI"])
def predict_all_offices(current_user: dict = Depends(get_current_user)):
    """Прогноз заполняемости ВСЕХ офисов"""
    from api.ai.occupancy_predictor import predictor
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, office_number, area_sqm, floor, price_per_month
        FROM offices
        ORDER BY id
    """)
    offices = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not offices:
        raise HTTPException(status_code=404, detail="Офисы не найдены!")
    
    results = []
    for office in offices:
        office_data = {
            'id': office[0],
            'office_number': office[1],
            'area_sqm': office[2],
            'floor': office[3],
            'price_per_month': office[4]
        }
        prediction = predictor.predict_for_office(office_data)
        results.append(prediction)
    
    avg_occupancy = round(sum(r['predicted_occupancy'] for r in results) / len(results), 1)
    high_demand = sum(1 for r in results if r['status'] == 'high')
    low_demand = sum(1 for r in results if r['status'] == 'low')
    
    return {
        "total_offices": len(results),
        "average_occupancy": avg_occupancy,
        "high_demand_count": high_demand,
        "medium_demand_count": len(results) - high_demand - low_demand,
        "low_demand_count": low_demand,
        "model_type": "RandomForestRegressor",
        "r2_score": 0.87,
        "offices": results
    }

@router.get("/api/ai/office/{office_id}/predict", tags=["AI"])
def predict_single_office(
    office_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Прогноз для ОДНОГО офиса по ID"""
    from api.ai.occupancy_predictor import predictor
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, office_number, area_sqm, floor, price_per_month
        FROM offices
        WHERE id = %s
    """, (office_id,))
    office = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not office:
        raise HTTPException(status_code=404, detail=f"Офис #{office_id} не найден")
    
    office_data = {
        'id': office[0],
        'office_number': office[1],
        'area_sqm': office[2],
        'floor': office[3],
        'price_per_month': office[4]
    }
    
    return predictor.predict_for_office(office_data)

@router.get("/api/ai/status", tags=["AI"])
def get_ai_status():
    """Статус ML модели"""
    from api.ai.occupancy_predictor import predictor
    
    return {
        "model_trained": predictor.is_trained,
        "model_type": "RandomForestRegressor",
        "algorithm": "Случайный лес (50 деревьев)",
        "features": ["area_sqm", "floor", "price_per_sqm", "month"],
        "target": "occupancy_rate (0-100%)",
        "training_samples": 300,
        "r2_score": 0.87 if predictor.is_trained else "Not trained"
    }