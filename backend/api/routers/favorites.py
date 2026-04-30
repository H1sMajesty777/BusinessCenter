# backend/api/routers/favorites.py

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from api.database import get_db
from api.security import get_current_user
from api.models.favorite import FavoriteCreate, FavoriteResponse
from api.rate_limiter import limiter, RATE_LIMITS

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])


@router.get("", response_model=List[dict])
@limiter.limit(RATE_LIMITS["authenticated"])
def get_favorites(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Получить все избранные офисы текущего пользователя
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT f.id, f.office_id, f.created_at,
                   o.office_number, o.floor, o.area_sqm, o.price_per_month, o.is_free
            FROM favorites f
            JOIN offices o ON f.office_id = o.id
            WHERE f.user_id = %s
            ORDER BY f.created_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        
        return [
            {
                "id": r['id'],
                "office_id": r['office_id'],
                "office_number": r['office_number'],
                "floor": r['floor'],
                "area_sqm": float(r['area_sqm']),
                "price_per_month": float(r['price_per_month']),
                "is_free": r['is_free'],
                "created_at": str(r['created_at'])
            }
            for r in rows
        ]
    finally:
        cursor.close()
        conn.close()


@router.post("", status_code=201)
@limiter.limit(RATE_LIMITS["authenticated"])
def add_favorite(
    request: Request,
    favorite: FavoriteCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Добавить офис в избранное
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли офис
        cursor.execute("SELECT id FROM offices WHERE id = %s", (favorite.office_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        # Добавляем в избранное (ON CONFLICT игнорирует дубликаты)
        cursor.execute("""
            INSERT INTO favorites (user_id, office_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id, office_id) DO NOTHING
            RETURNING id
        """, (user_id, favorite.office_id))
        
        row = cursor.fetchone()
        conn.commit()
        
        if row:
            return {"message": "Офис добавлен в избранное", "id": row['id']}
        else:
            return {"message": "Офис уже в избранном"}
    finally:
        cursor.close()
        conn.close()


@router.delete("/{office_id}")
@limiter.limit(RATE_LIMITS["authenticated"])
def remove_favorite(
    request: Request,
    office_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Удалить офис из избранного
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM favorites WHERE user_id = %s AND office_id = %s RETURNING id",
            (user_id, office_id)
        )
        
        if cursor.fetchone():
            conn.commit()
            return {"message": "Офис удалён из избранного"}
        else:
            raise HTTPException(status_code=404, detail="Офис не найден в избранном")
    finally:
        cursor.close()
        conn.close()


@router.get("/check/{office_id}")
@limiter.limit(RATE_LIMITS["authenticated"])
def check_favorite(
    request: Request,
    office_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Проверить, находится ли офис в избранном
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id FROM favorites WHERE user_id = %s AND office_id = %s",
            (user_id, office_id)
        )
        is_favorite = cursor.fetchone() is not None
        
        return {"is_favorite": is_favorite}
    finally:
        cursor.close()
        conn.close()