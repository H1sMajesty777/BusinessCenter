# backend/api/routers/ai_rental_prediction.py
# -*- coding: utf-8 -*-
"""
Роуты для AI прогноза аренды офисов
Расширенная версия с аналитикой и рекомендациями
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
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


def require_admin(current_user: dict):
    """Проверка роли: только админ"""
    if current_user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Только администраторы")


# ===================================================================
# ENDPOINTS
# ===================================================================

@router.post("/train", response_model=Dict[str, Any])
def train_model(
    force: bool = Query(False, description="Принудительное переобучение"),
    current_user: dict = Depends(get_current_user)
):
    """
    Обучение ML модели на исторических данных
    
    Доступ: Только АДМИН
    
    Args:
        force: Принудительное переобучение даже если модель уже есть
    
    Returns:
        dict: Результаты обучения с метриками качества
    """
    require_admin(current_user)
    
    conn = get_db()
    
    try:
        result = rental_predictor.train(conn, force_retrain=force)
        
        status_code = 200 if result.get('status') != 'error' else 500
        
        return {
            "success": result.get('status') != 'error',
            "message": result.get('message', "Обучение завершено"),
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обучения: {str(e)}")
    finally:
        conn.close()


@router.get("/model/info", response_model=Dict[str, Any])
def get_model_info(current_user: dict = Depends(get_current_user)):
    """
    Информация о текущей модели
    
    Доступ: Админ/Менеджер
    
    Returns:
        dict: Информация о модели (тип, признаки, важность)
    """
    require_admin_or_manager(current_user)
    
    return rental_predictor.get_model_info()


@router.get("/office/{office_id}", response_model=Dict[str, Any])
def predict_office_rental(
    office_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Прогноз вероятности аренды конкретного офиса
    
    Доступ: Все авторизованные
    
    Args:
        office_id: ID офиса для прогноза
    
    Returns:
        dict: Прогноз с вероятностью, категорией и факторами
    """
    conn = get_db()
    
    try:
        result = rental_predictor.predict_probability(conn, office_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        # Добавляем рекомендации
        result["recommendations"] = _generate_recommendations(result)
        
        return result
    
    finally:
        conn.close()


@router.get("/offices", response_model=List[Dict[str, Any]])
def predict_multiple_offices(
    office_ids: str = Query(..., description="Список ID офисов через запятую"),
    current_user: dict = Depends(get_current_user)
):
    """
    Массовый прогноз для нескольких офисов
    
    Доступ: Админ/Менеджер
    
    Args:
        office_ids: Строка с ID через запятую (например: "1,5,13,19")
    
    Returns:
        List[dict]: Список прогнозов для каждого офиса
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
        
        # Добавляем рекомендации
        for result in results:
            if "error" not in result:
                result["recommendations"] = _generate_recommendations(result)
        
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
    min_price: Optional[float] = Query(None, description="Минимальная цена"),
    max_price: Optional[float] = Query(None, description="Максимальная цена"),
    min_probability: Optional[float] = Query(None, ge=0, le=1, description="Минимальная вероятность"),
    category: Optional[str] = Query(None, pattern="^(high|medium|low)$", description="Фильтр по категории"),
    sort_by: str = Query("probability", description="Сортировка: probability, price, floor"),
    limit: int = Query(50, ge=1, le=200, description="Максимальное количество результатов"),
    current_user: dict = Depends(get_current_user)
):
    """
    Сводка прогнозов по всем свободным офисам с фильтрацией
    
    Доступ: Админ/Менеджер
    
    Args:
        floor: Фильтр по этажу
        min_price: Минимальная цена
        max_price: Максимальная цена
        min_probability: Минимальная вероятность (0.0-1.0)
        category: Фильтр по категории (high/medium/low)
        sort_by: Поле для сортировки
        limit: Лимит результатов
    
    Returns:
        dict: Сводная статистика и список офисов с прогнозами
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Получаем свободные офисы с фильтрацией
        query = """
            SELECT id, office_number, floor, area_sqm, price_per_month, description
            FROM offices 
            WHERE is_free = TRUE
        """
        params = []
        
        if floor is not None:
            query += " AND floor = %s"
            params.append(floor)
        
        if min_price is not None:
            query += " AND price_per_month >= %s"
            params.append(min_price)
        
        if max_price is not None:
            query += " AND price_per_month <= %s"
            params.append(max_price)
        
        query += " ORDER BY floor, office_number"
        
        cursor.execute(query, params)
        offices = cursor.fetchall()
        
        if not offices:
            return {
                "total_offices": 0,
                "by_category": {},
                "offices": [],
                "statistics": {
                    "avg_probability": 0,
                    "high_count": 0,
                    "medium_count": 0,
                    "low_count": 0
                }
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
                    "area_sqm": float(office['area_sqm']),
                    "price_per_month": float(office['price_per_month']),
                    "probability": pred['probability'],
                    "probability_percent": pred['probability_percent'],
                    "category": pred['category'],
                    "description": pred['description']
                })
        
        # Применяем фильтры
        if min_probability is not None:
            predictions = [p for p in predictions if p['probability'] >= min_probability]
        
        if category is not None:
            predictions = [p for p in predictions if p['category'] == category]
        
        # Сортировка
        reverse = sort_by != "price"  # price сортируем по возрастанию
        predictions.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
        
        # Ограничиваем количество
        predictions = predictions[:limit]
        
        # Статистика по категориям
        by_category = {}
        for cat in ['high', 'medium', 'low']:
            cat_predictions = [p for p in predictions if p['category'] == cat]
            if cat_predictions:
                by_category[cat] = {
                    "count": len(cat_predictions),
                    "avg_probability": round(sum(p['probability'] for p in cat_predictions) / len(cat_predictions), 3),
                    "offices": [p['office_number'] for p in cat_predictions]
                }
        
        # Общая статистика
        high_count = len([p for p in predictions if p['category'] == 'high'])
        medium_count = len([p for p in predictions if p['category'] == 'medium'])
        low_count = len([p for p in predictions if p['category'] == 'low'])
        
        return {
            "total_offices": len(predictions),
            "by_category": by_category,
            "statistics": {
                "avg_probability": round(sum(p['probability'] for p in predictions) / len(predictions), 3) if predictions else 0,
                "high_count": high_count,
                "medium_count": medium_count,
                "low_count": low_count,
                "potential_monthly_income": round(sum(p['price_per_month'] for p in predictions if p['category'] == 'high'), 2)
            },
            "offices": predictions
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
    Подробное объяснение прогноза для офиса
    
    Доступ: Админ/Менеджер
    
    Args:
        office_id: ID офиса
    
    Returns:
        dict: Детальное объяснение с факторами влияния и рекомендациями
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        result = rental_predictor.predict_probability(conn, office_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        # Получаем детальную статистику офиса
        cursor.execute("""
            SELECT 
                o.office_number, o.floor, o.area_sqm, o.price_per_month,
                (SELECT COUNT(*) FROM office_views WHERE office_id = %s) as total_views,
                (SELECT COUNT(*) FROM applications WHERE office_id = %s) as total_applications,
                (SELECT COUNT(*) FROM contracts WHERE office_id = %s) as total_contracts,
                (SELECT COUNT(*) FROM offices WHERE floor = o.floor AND is_free = TRUE) as free_on_floor,
                (SELECT COUNT(*) FROM offices WHERE floor = o.floor) as total_on_floor
            FROM offices o
            WHERE o.id = %s
        """, (office_id, office_id, office_id, office_id))
        
        office_stats = cursor.fetchone()
        
        if not office_stats:
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        competition_ratio = office_stats['free_on_floor'] / office_stats['total_on_floor'] if office_stats['total_on_floor'] > 0 else 1
        
        result['detailed_stats'] = {
            "office_number": office_stats['office_number'],
            "floor": office_stats['floor'],
            "area_sqm": float(office_stats['area_sqm']),
            "price_per_month": float(office_stats['price_per_month']),
            "price_per_sqm": round(float(office_stats['price_per_month']) / float(office_stats['area_sqm']), 2),
            "total_views": office_stats['total_views'] or 0,
            "total_applications": office_stats['total_applications'] or 0,
            "total_contracts": office_stats['total_contracts'] or 0,
            "competition_on_floor": f"{office_stats['free_on_floor']} / {office_stats['total_on_floor']}",
            "competition_ratio": round(competition_ratio, 2)
        }
        
        # Генерация подробных рекомендаций
        result['recommendations'] = _generate_detailed_recommendations(result, office_stats)
        
        return result
    
    finally:
        cursor.close()
        conn.close()


@router.post("/sync", response_model=Dict[str, Any])
def sync_and_retrain(current_user: dict = Depends(get_current_user)):
    """
    Синхронизация данных и переобучение модели
    
    Доступ: Только АДМИН
    
    Returns:
        dict: Результаты синхронизации и обучения
    """
    require_admin(current_user)
    
    conn = get_db()
    
    try:
        # Обучаем модель заново
        result = rental_predictor.train(conn, force_retrain=True)
        
        return {
            "success": True,
            "message": "Модель успешно переобучена на актуальных данных",
            "details": result
        }
    
    finally:
        conn.close()


@router.get("/trends", response_model=Dict[str, Any])
def get_rental_trends(
    days: int = Query(30, ge=7, le=365, description="Период анализа в днях"),
    current_user: dict = Depends(get_current_user)
):
    """
    Тренды аренды офисов
    
    Доступ: Админ/Менеджер
    
    Args:
        days: Период анализа в днях
    
    Returns:
        dict: Аналитика трендов
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Просмотры по дням
        cursor.execute("""
            SELECT 
                DATE(viewed_at) as date,
                COUNT(*) as views,
                COUNT(DISTINCT user_id) as unique_users
            FROM office_views
            WHERE viewed_at > NOW() - INTERVAL '%s days'
            GROUP BY DATE(viewed_at)
            ORDER BY date
        """, (days,))
        
        views_trend = cursor.fetchall()
        
        # Заявки по дням
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as applications,
                COUNT(CASE WHEN status_id = 2 THEN 1 END) as approved
            FROM applications
            WHERE created_at > NOW() - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (days,))
        
        applications_trend = cursor.fetchall()
        
        # Договоры по дням
        cursor.execute("""
            SELECT 
                DATE(signed_at) as date,
                COUNT(*) as contracts,
                COALESCE(SUM(total_amount), 0) as total_amount
            FROM contracts
            WHERE signed_at > NOW() - INTERVAL '%s days'
            GROUP BY DATE(signed_at)
            ORDER BY date
        """, (days,))
        
        contracts_trend = cursor.fetchall()
        
        return {
            "period_days": days,
            "views_trend": [
                {"date": str(r['date']), "views": r['views'], "unique_users": r['unique_users']}
                for r in views_trend
            ],
            "applications_trend": [
                {"date": str(r['date']), "applications": r['applications'], "approved": r['approved']}
                for r in applications_trend
            ],
            "contracts_trend": [
                {"date": str(r['date']), "contracts": r['contracts'], "total_amount": float(r['total_amount'])}
                for r in contracts_trend
            ]
        }
    
    finally:
        cursor.close()
        conn.close()


# ===================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РЕКОМЕНДАЦИЙ
# ===================================================================

def _generate_recommendations(prediction: Dict[str, Any]) -> List[str]:
    """Генерация рекомендаций на основе прогноза"""
    category = prediction.get('category', 'medium')
    probability = prediction.get('probability', 0.5)
    
    if category == 'low':
        return [
            "Низкая активность по офису",
            "Рекомендации: снизьте цену на 10-15%, добавьте больше фото, активируйте рекламу",
            "Рассмотрите специальные предложения: первый месяц в подарок или скидка 20% на 3 месяца"
        ]
    elif category == 'high':
        return [
            "Высокий спрос на офис!",
            "Действуйте быстро: подготовьте договор, свяжитесь с заинтересованными клиентами",
            "Возможно повышение цены на 5-10% при продлении договора"
        ]
    else:  # medium
        return [
            "Средняя вероятность аренды",
            "Рекомендации: улучшите описание, добавьте виртуальный тур",
            "Предложите персональную презентацию офиса заинтересованным клиентам"
        ]


def _generate_detailed_recommendations(
    prediction: Dict[str, Any], 
    office_stats: Any
) -> Dict[str, Any]:
    """Генерация детальных рекомендаций с конкретными действиями"""
    category = prediction.get('category', 'medium')
    
    recommendations = {
        "priority": "high" if category == 'high' else "medium" if category == 'medium' else "low",
        "actions": [],
        "expected_impact": ""
    }
    
    if category == 'low':
        recommendations["actions"] = [
            {"action": "Снижение цены", "details": "Рекомендуемое снижение: 10-15%", "impact": "high"},
            {"action": "Улучшение презентации", "details": "Добавить профессиональные фото и виртуальный тур", "impact": "medium"},
            {"action": "Рекламная кампания", "details": "Запустить таргетированную рекламу", "impact": "medium"}
        ]
        recommendations["expected_impact"] = "Повышение вероятности аренды на 20-30%"
    
    elif category == 'high':
        recommendations["actions"] = [
            {"action": "Быстрое оформление", "details": "Подготовить договор и документы заранее", "impact": "critical"},
            {"action": "Персональные консультации", "details": "Связаться со всеми заинтересованными", "impact": "high"},
            {"action": "Гибкие условия", "details": "Предложить индивидуальные условия аренды", "impact": "medium"}
        ]
        recommendations["expected_impact"] = "Заключение договора в ближайшее время"
    
    else:  # medium
        recommendations["actions"] = [
            {"action": "Улучшение описания", "details": "Добавить больше деталей и преимуществ", "impact": "medium"},
            {"action": "Фото/видео материалы", "details": "Профессиональная съёмка офиса", "impact": "medium"},
            {"action": "Спецпредложение", "details": "Акция на первый месяц аренды", "impact": "high"}
        ]
        recommendations["expected_impact"] = "Повышение вероятности аренды на 10-15%"
    
    return recommendations
# Добавь в существующий файл эти эндпоинты:

@router.get("/models/compare", response_model=Dict[str, Any])
def compare_models(current_user: dict = Depends(get_current_user)):
    """Сравнение всех моделей в ансамбле"""
    require_admin_or_manager(current_user)
    
    if not advanced_predictor.is_trained:
        raise HTTPException(status_code=400, detail="Model not trained yet")
    
    return {
        "models": list(advanced_predictor.models.keys()),
        "ensemble_size": len(advanced_predictor.models),
        "feature_count": len(advanced_predictor.feature_columns) if advanced_predictor.feature_columns else 0
    }

@router.get("/features/importance", response_model=Dict[str, Any])
def get_feature_importance(current_user: dict = Depends(get_current_user)):
    """Важность признаков для разных моделей"""
    require_admin_or_manager(current_user)
    
    if not advanced_predictor.is_trained:
        raise HTTPException(status_code=400, detail="Model not trained yet")
    
    importance = {}
    for name, model in advanced_predictor.models.items():
        if name != 'neural_network' and hasattr(model, 'feature_importances_'):
            imp = model.feature_importances_
            importance[name] = {
                "top_features": [
                    {"feature": advanced_predictor.feature_columns[i], "importance": float(imp[i])}
                    for i in np.argsort(imp)[-5:][::-1]
                ]
            }
    
    return importance