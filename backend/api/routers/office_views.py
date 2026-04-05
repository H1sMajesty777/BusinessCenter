# -*- coding: utf-8 -*-
"""
Роуты для просмотров офисов (Office Views)
Отслеживание просмотров офисов пользователями для аналитики
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime
from api.database import get_db
from api.security import decode_token
from api.models.office_view import OfficeViewCreate, OfficeViewResponse
from api.rate_limiter import limiter, RATE_LIMITS


router = APIRouter(prefix="/api/office-views", tags=["OfficeViews"])
security = HTTPBearer(auto_error=False)



def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Получить текущего пользователя из JWT токена
    
    Args:
        credentials: JWT токен из заголовка Authorization
    
    Returns:
        dict: Payload токена (sub, role_id, login, etc.)
    
    Raises:
        HTTPException: 401 если токена нет или он неверный
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Нет токена")
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    return payload


def require_admin_or_manager(current_user: dict):
    """
    Проверка роли: только админ или менеджер
    
    Args:
        current_user: Данные текущего пользователя из токена
    
    Raises:
        HTTPException: 403 если роль не admin (1) или manager (2)
    """
    if current_user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Только админ и менеджер")


# ===================================================================
# ENDPOINTS
# ===================================================================

@router.post("", status_code=201, response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def create_office_view(request: Request, view: OfficeViewCreate = Body(...), current_user: dict = Depends(get_current_user)):
    """
    Запись просмотра офиса
    
    Доступ: Все авторизованные
    
    Args:
        view: Данные просмотра (office_id, duration_seconds, is_contacted)
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: ID созданной записи и сообщение
    
    Raises:
        HTTPException: 404 если офис не найден
    
    Note:
        user_id берётся автоматически из токена
        viewed_at устанавливается автоматически (текущее время)
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка что офис существует
        cursor.execute("SELECT id FROM offices WHERE id = %s", (view.office_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        # Создание записи о просмотре
        cursor.execute(
            """INSERT INTO office_views (user_id, office_id, viewed_at, duration_seconds, is_contacted) 
               VALUES (%s, %s, %s, %s, %s) RETURNING id, viewed_at""",
            (user_id, view.office_id, datetime.now(), view.duration_seconds, view.is_contacted)
        )
        row = cursor.fetchone()
        conn.commit()
        
        return {
            "id": row['id'], 
            "message": "Просмотр записан",
            "viewed_at": str(row['viewed_at']) if row['viewed_at'] else None
        }
    
    finally:
        cursor.close()
        conn.close()


@router.get("", response_model=List[dict])
@limiter.limit(RATE_LIMITS["authenticated"])
def get_all_office_views(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: dict = Depends(get_current_user)
):
    """
    Просмотр всех записей о просмотрах
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        limit: Максимальное количество записей для возврата (1-1000)
        current_user: Текущий пользователь из токена
    
    Returns:
        List[dict]: Список всех записей о просмотрах с данными пользователей и офисов
    
    Raises:
        HTTPException: 403 если роль не admin/manager
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT v.id, v.user_id, u.login, v.office_id, o.office_number, 
                   v.viewed_at, v.duration_seconds, v.is_contacted 
            FROM office_views v 
            LEFT JOIN users u ON v.user_id = u.id 
            JOIN offices o ON v.office_id = o.id 
            ORDER BY v.viewed_at DESC 
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        
        return [
            {
                "id": r['id'],
                "user_id": r['user_id'],
                "user_login": r['login'],
                "office_id": r['office_id'],
                "office_number": r['office_number'],
                "viewed_at": str(r['viewed_at']),
                "duration_seconds": r['duration_seconds'],
                "is_contacted": r['is_contacted']
            }
            for r in rows
        ]
    
    finally:
        cursor.close()
        conn.close()


@router.get("/my", response_model=List[dict])
@limiter.limit(RATE_LIMITS["authenticated"])
def get_my_office_views(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Просмотр своих просмотров офисов
    
    Доступ: Все авторизованные
    
    Args:
        current_user: Текущий пользователь из токена
    
    Returns:
        List[dict]: Список просмотров текущего пользователя
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT v.id, v.office_id, o.office_number, v.viewed_at, 
                   v.duration_seconds, v.is_contacted 
            FROM office_views v 
            JOIN offices o ON v.office_id = o.id 
            WHERE v.user_id = %s 
            ORDER BY v.viewed_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        
        return [
            {
                "id": r['id'],
                "office_id": r['office_id'],
                "office_number": r['office_number'],
                "viewed_at": str(r['viewed_at']),
                "duration_seconds": r['duration_seconds'],
                "is_contacted": r['is_contacted']
            }
            for r in rows
        ]
    
    finally:
        cursor.close()
        conn.close()


@router.get("/office/{office_id}", response_model=List[dict])
@limiter.limit(RATE_LIMITS["authenticated"])
def get_office_views(
    request: Request,
    office_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Просмотр всех просмотров конкретного офиса
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        office_id: ID офиса
        current_user: Текущий пользователь из токена
    
    Returns:
        List[dict]: Список всех просмотров указанного офиса
    
    Raises:
        HTTPException: 403 если роль не admin/manager
        HTTPException: 404 если офис не найден
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка что офис существует
        cursor.execute("SELECT id FROM offices WHERE id = %s", (office_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        cursor.execute("""
            SELECT v.id, v.user_id, u.login, v.office_id, o.office_number, 
                   v.viewed_at, v.duration_seconds, v.is_contacted 
            FROM office_views v 
            LEFT JOIN users u ON v.user_id = u.id 
            JOIN offices o ON v.office_id = o.id 
            WHERE v.office_id = %s 
            ORDER BY v.viewed_at DESC
        """, (office_id,))
        rows = cursor.fetchall()
        
        return [
            {
                "id": r['id'],
                "user_id": r['user_id'],
                "user_login": r['login'],
                "office_id": r['office_id'],
                "office_number": r['office_number'],
                "viewed_at": str(r['viewed_at']),
                "duration_seconds": r['duration_seconds'],
                "is_contacted": r['is_contacted']
            }
            for r in rows
        ]
    
    finally:
        cursor.close()
        conn.close()


@router.get("/stats", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def get_office_views_stats(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Статистика просмотров офисов
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: Статистика по просмотрам (общее количество, по офисам, за сегодня)
    
    Raises:
        HTTPException: 403 если роль не admin/manager
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Общее количество просмотров
        cursor.execute("SELECT COUNT(*) as count FROM office_views")
        total = cursor.fetchone()['count']
        
        # Просмотры за сегодня
        cursor.execute("""
            SELECT COUNT(*) as count FROM office_views 
            WHERE DATE(viewed_at) = CURRENT_DATE
        """)
        today = cursor.fetchone()['count']
        
        # Топ офисов по просмотрам
        cursor.execute("""
            SELECT o.office_number, COUNT(v.id) as views 
            FROM office_views v 
            JOIN offices o ON v.office_id = o.id 
            GROUP BY o.office_number 
            ORDER BY views DESC 
            LIMIT 10
        """)
        top_offices = cursor.fetchall()
        
        # Средняя длительность просмотра (в секундах)
        cursor.execute("""
            SELECT COALESCE(AVG(duration_seconds), 0) as avg_duration 
            FROM office_views 
            WHERE duration_seconds IS NOT NULL
        """)
        avg_duration = cursor.fetchone()['avg_duration']
        
        return {
            "total_views": total,
            "today_views": today,
            "average_duration_seconds": round(float(avg_duration), 2) if avg_duration else 0,
            "top_offices": [
                {"office_number": r['office_number'], "views": r['views']} 
                for r in top_offices
            ]
        }
    
    finally:
        cursor.close()
        conn.close()


@router.put("/{view_id}/contact", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def mark_as_contacted(
    request: Request,
    view_id: int,
    is_contacted: bool = Body(..., embed=True),
    current_user: dict = Depends(get_current_user)
):
    """
    Отметить просмотр как "связался" / "не связался"
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        view_id: ID записи о просмотре
        is_contacted: Флаг связался ли пользователь
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: Сообщение об успешном обновлении
    
    Raises:
        HTTPException: 404 если запись не найдена
        HTTPException: 403 если роль не admin/manager
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE office_views SET is_contacted = %s WHERE id = %s RETURNING id",
            (is_contacted, view_id)
        )
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Запись о просмотре не найдена")
        
        conn.commit()
        
        return {
            "message": f"Статус просмотра {view_id} обновлён",
            "is_contacted": is_contacted
        }
    
    finally:
        cursor.close()
        conn.close()


@router.delete("/{view_id}", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def delete_office_view(
    request: Request,
    view_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Удаление записи о просмотре
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        view_id: ID записи о просмотре
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: Сообщение об успешном удалении
    
    Raises:
        HTTPException: 404 если запись не найдена
        HTTPException: 403 если роль не admin/manager
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM office_views WHERE id = %s RETURNING id", (view_id,))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Запись о просмотре не найдена")
        
        conn.commit()
        
        return {"message": f"Запись о просмотре {view_id} удалена"}
    
    finally:
        cursor.close()
        conn.close()