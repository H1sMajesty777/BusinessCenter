# -*- coding: utf-8 -*-
"""
Роуты для AI прогноза аренды офисов
Предсказание вероятности: high / medium / low
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from api.database import get_db
from api.security import decode_token
from api.ml_models.office_rental_prediction import rental_predictor

router = APIRouter(prefix="/api/ai/rental-prediction", tags=["AI Rental Prediction"])
security = HTTPBearer(auto_error=False)


# ===================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ===================================================================

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получить текущего пользователя из токена"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Нет токена")
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    return payload


def require_admin_or_manager(current_user: dict):
    """Проверка роли: только админ или менеджер"""
    if current_user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Только админ и менеджер")


# ===================================================================
# ENDPOINTS
# ===================================================================

@router.post("/train", response_model=Dict[str, Any])
def train_model(current_user: dict = Depends(get_current_user)):
    """
    🔧 Обучение ML модели на исторических данных
    
    Доступ: Только АДМИН
    
    Returns:
        dict: Результаты обучения
    
    Note:
        Запускается один раз или при добавлении новых данных
        Требуется минимум 10 исторических записей
    """
    if current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Только администраторы")
    
    conn = get_db()
    
    try:
        result = rental_predictor.train(conn)
        return {
            "success": True,
            "message": "Модель успешно обучена" if result['status'] == 'trained' else "Использована дефолтная модель",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обучения: {str(e)}")
    finally:
        conn.close()


@router.get("/office/{office_id}", response_model=Dict[str, Any])
def predict_office_rental(
    office_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    🎯 Прогноз вероятности аренды конкретного офиса
    
    Доступ: Все авторизованные
    
    Args:
        office_id: ID офиса для прогноза
    
    Returns:
        dict: Прогноз с вероятностью и категорией
    
    Example:
        GET /api/ai/rental-prediction/office/13
        
        Response:
        {
            "office_id": 13,
            "probability": 0.78,
            "probability_percent": 78.0,
            "category": "high",
            "description": "Высокая вероятность аренды в этом месяце",
            "top_factors": [
                {"feature": "application_count", "importance": 0.35},
                {"feature": "contact_rate", "importance": 0.28},
                {"feature": "view_count", "importance": 0.15}
            ]
        }
    """
    conn = get_db()
    
    try:
        result = rental_predictor.predict_probability(conn, office_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    
    finally:
        conn.close()


@router.get("/offices", response_model=List[Dict[str, Any]])
def predict_multiple_offices(
    office_ids: str = Query(..., description="Список ID офисов через запятую, например: 1,5,13"),
    current_user: dict = Depends(get_current_user)
):
    """
    📊 Массовый прогноз для нескольких офисов
    
    Доступ: Админ/Менеджер
    
    Args:
        office_ids: Строка с ID через запятую (например: "1,5,13,19")
    
    Returns:
        List[dict]: Список прогнозов для каждого офиса
    
    Example:
        GET /api/ai/rental-prediction/offices?office_ids=1,5,13,19
    """
    require_admin_or_manager(current_user)
    
    try:
        ids = [int(x.strip()) for x in office_ids.split(',') if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат office_ids")
    
    if not ids:
        raise HTTPException(status_code=400, detail="Укажите хотя бы один office_id")
    
    conn = get_db()
    
    try:
        results = rental_predictor.predict_batch(conn, ids)
        
        # Фильтруем ошибки
        valid_results = [r for r in results if "error" not in r]
        
        if not valid_results:
            raise HTTPException(status_code=404, detail="Ни один офис не найден")
        
        return valid_results
    
    finally:
        conn.close()


@router.get("/summary", response_model=Dict[str, Any])
def get_prediction_summary(
    floor: Optional[int] = Query(None, description="Фильтр по этажу"),
    min_probability: Optional[float] = Query(None, ge=0, le=1, description="Минимальная вероятность"),
    category: Optional[str] = Query(None, pattern="^(high|medium|low)$", description="Фильтр по категории"),
    current_user: dict = Depends(get_current_user)
):
    """
    📈 Сводка прогнозов по всем свободным офисам
    
    Доступ: Админ/Менеджер
    
    Args:
        floor: Фильтр по этажу
        min_probability: Минимальная вероятность (0.0-1.0)
        category: Фильтр по категории (high/medium/low)
    
    Returns:
        dict: Сводная статистика и список офисов с прогнозами
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Получаем свободные офисы
        query = "SELECT id, office_number, floor, price_per_month FROM offices WHERE is_free = TRUE"
        params = []
        
        if floor is not None:
            query += " AND floor = %s"
            params.append(floor)
        
        query += " ORDER BY id"
        
        cursor.execute(query, params)
        offices = cursor.fetchall()
        
        if not offices:
            return {
                "total_offices": 0,
                "by_category": {},
                "offices": []
            }
        
        # Получаем прогнозы для каждого офиса
        predictions = []
        for office in offices:
            pred = rental_predictor.predict_probability(conn, office['id'])
            if "error" not in pred:
                predictions.append({
                    "office_id": office['id'],
                    "office_number": office['office_number'],
                    "floor": office['floor'],
                    "price_per_month": float(office['price_per_month']),
                    "probability": pred['probability'],
                    "category": pred['category'],
                    "description": pred['description']
                })
        
        # Применяем фильтры
        if min_probability is not None:
            predictions = [p for p in predictions if p['probability'] >= min_probability]
        
        if category is not None:
            predictions = [p for p in predictions if p['category'] == category]
        
        # Статистика по категориям
        by_category = {}
        for cat in ['high', 'medium', 'low']:
            count = sum(1 for p in predictions if p['category'] == cat)
            if count > 0:
                by_category[cat] = {
                    "count": count,
                    "offices": [p['office_number'] for p in predictions if p['category'] == cat]
                }
        
        return {
            "total_offices": len(predictions),
            "by_category": by_category,
            "avg_probability": round(sum(p['probability'] for p in predictions) / len(predictions), 3) if predictions else 0,
            "offices": sorted(predictions, key=lambda x: x['probability'], reverse=True)
        }
    
    finally:
        cursor.close()
        conn.close()


@router.get("/explain/{office_id}", response_model=Dict[str, Any])
def explain_prediction(
    office_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    🔍 Подробное объяснение прогноза для офиса
    
    Доступ: Админ/Менеджер
    
    Args:
        office_id: ID офиса
    
    Returns:
        dict: Детальное объяснение с факторами влияния
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    
    try:
        result = rental_predictor.predict_probability(conn, office_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        # Добавляем рекомендации на основе прогноза
        recommendations = []
        
        if result['category'] == 'low':
            recommendations = [
                "Рассмотрите снижение цены для повышения привлекательности",
                "Добавьте больше фото и деталей в описание",
                "Предложите пробный период аренды"
            ]
        elif result['category'] == 'high':
            recommendations = [
                "Подготовьте договор для быстрого оформления",
                "Свяжитесь с заинтересованными клиентами",
                "Рассмотрите возможность повышения цены при продлении"
            ]
        else:  # medium
            recommendations = [
                "Увеличьте видимость офиса в каталоге",
                "Предложите гибкие условия аренды",
                "Проведите персональную презентацию для заинтересованных"
            ]
        
        result['recommendations'] = recommendations
        
        return result
    
    finally:
        conn.close()