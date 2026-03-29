# -*- coding: utf-8 -*-
"""
Роуты для управления офисами бизнес-центра
CRUD операции для офисов: создание, чтение, обновление, удаление
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import json
from api.database import get_db
from api.security import decode_token
from api.models.office import OfficeCreate, OfficeUpdate, OfficeResponse

# ✅ Router с правильным префиксом
router = APIRouter(prefix="/api/offices", tags=["Offices"])
security = HTTPBearer(auto_error=False)


# ===================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ===================================================================

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

@router.get("", response_model=List[OfficeResponse])
def get_offices(
    floor: Optional[int] = Query(None, description="Фильтр по этажу"),
    max_price: Optional[float] = Query(None, description="Максимальная цена"),
    is_free: Optional[bool] = Query(None, description="Только свободные офисы")
):
    """
    Каталог офисов — фильтрация и поиск
    
    Доступ: Все (чтение без авторизации)
    
    Args:
        floor: Фильтр по этажу (опционально)
        max_price: Максимальная цена аренды (опционально)
        is_free: Фильтр по статусу доступности (опционально)
    
    Returns:
        List[OfficeResponse]: Список офисов с применёнными фильтрами
    
    Example:
        GET /api/offices?floor=2&max_price=30000&is_free=true
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT id, office_number, floor, area_sqm, price_per_month, 
                   description, amenities, is_free, created_at 
            FROM offices WHERE 1=1
        """
        params = []
        
        if floor is not None:
            query += " AND floor = %s"
            params.append(floor)
        
        if max_price is not None:
            query += " AND price_per_month <= %s"
            params.append(max_price)
        
        # ✅ Правильная обработка boolean
        if is_free is not None:
            query += " AND is_free = %s"
            params.append(bool(is_free))
        
        query += " ORDER BY floor, office_number"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for r in rows:
            # ✅ Безопасный парсинг JSON
            try:
                amenities_data = json.loads(r['amenities']) if r['amenities'] else None
            except (json.JSONDecodeError, TypeError, Exception):
                amenities_data = None
            
            result.append(
                OfficeResponse(
                    id=r['id'],
                    office_number=r['office_number'],
                    floor=r['floor'],
                    area_sqm=float(r['area_sqm']),
                    price_per_month=float(r['price_per_month']),
                    description=r['description'] if r['description'] else None,
                    amenities=amenities_data,
                    is_free=bool(r['is_free']),
                    created_at=r['created_at']
                )
            )
        
        return result
    
    except Exception as e:
        # ✅ Показываем ошибку для дебага
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.post("", status_code=201, response_model=OfficeResponse)
def create_office(office: OfficeCreate, current_user: dict = Depends(get_current_user)):
    """
    Создание нового офиса
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        office: Данные офиса для создания
        current_user: Текущий пользователь из токена
    
    Returns:
        OfficeResponse: Данные созданного офиса
    
    Raises:
        HTTPException: 403 если роль не admin/manager
        HTTPException: 500 если ошибка при создании
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO offices (office_number, floor, area_sqm, price_per_month, 
                                   description, amenities, is_free) 
               VALUES (%s, %s, %s, %s, %s, %s, %s) 
               RETURNING id, office_number, floor, area_sqm, price_per_month, 
                         description, amenities, is_free, created_at""",
            (
                office.office_number,
                office.floor,
                office.area_sqm,
                office.price_per_month,
                office.description,
                json.dumps(office.amenities, ensure_ascii=False) if office.amenities else None,
                office.is_free
            )
        )
        row = cursor.fetchone()
        conn.commit()
        
        # ✅ Безопасный парсинг JSON
        try:
            amenities_data = json.loads(row['amenities']) if row['amenities'] else None
        except (json.JSONDecodeError, TypeError, Exception):
            amenities_data = None
        
        return OfficeResponse(
            id=row['id'],
            office_number=row['office_number'],
            floor=row['floor'],
            area_sqm=float(row['area_sqm']),
            price_per_month=float(row['price_per_month']),
            description=row['description'] if row['description'] else None,
            amenities=amenities_data,
            is_free=bool(row['is_free']),
            created_at=row['created_at']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/{office_id}", response_model=OfficeResponse)
def get_office(office_id: int):
    """
    Получение данных офиса по ID
    
    Доступ: Все (чтение без авторизации)
    
    Args:
        office_id: ID офиса
    
    Returns:
        OfficeResponse: Данные офиса
    
    Raises:
        HTTPException: 404 если офис не найден
        HTTPException: 500 если ошибка при получении
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """SELECT id, office_number, floor, area_sqm, price_per_month, 
                      description, amenities, is_free, created_at 
               FROM offices WHERE id = %s""",
            (office_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        # ✅ Безопасный парсинг JSON
        try:
            amenities_data = json.loads(row['amenities']) if row['amenities'] else None
        except (json.JSONDecodeError, TypeError, Exception):
            amenities_data = None
        
        return OfficeResponse(
            id=row['id'],
            office_number=row['office_number'],
            floor=row['floor'],
            area_sqm=float(row['area_sqm']),
            price_per_month=float(row['price_per_month']),
            description=row['description'] if row['description'] else None,
            amenities=amenities_data,
            is_free=bool(row['is_free']),
            created_at=row['created_at']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.put("/{office_id}", response_model=OfficeResponse)
def update_office(office_id: int, office: OfficeUpdate, current_user: dict = Depends(get_current_user)):
    """
    Обновление данных офиса
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        office_id: ID офиса для обновления
        office: Новые данные офиса (только изменённые поля)
        current_user: Текущий пользователь из токена
    
    Returns:
        OfficeResponse: Обновлённые данные офиса
    
    Raises:
        HTTPException: 400 если нет данных для обновления
        HTTPException: 403 если роль не admin/manager
        HTTPException: 404 если офис не найден
        HTTPException: 500 если ошибка при обновлении
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if office.office_number is not None:
            updates.append("office_number = %s")
            params.append(office.office_number)
        
        if office.floor is not None:
            updates.append("floor = %s")
            params.append(office.floor)
        
        if office.area_sqm is not None:
            updates.append("area_sqm = %s")
            params.append(office.area_sqm)
        
        if office.price_per_month is not None:
            updates.append("price_per_month = %s")
            params.append(office.price_per_month)
        
        if office.description is not None:
            updates.append("description = %s")
            params.append(office.description)
        
        if office.amenities is not None:
            updates.append("amenities = %s")
            params.append(json.dumps(office.amenities, ensure_ascii=False))
        
        if office.is_free is not None:
            updates.append("is_free = %s")
            params.append(bool(office.is_free))
        
        if not updates:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")
        
        params.append(office_id)
        
        cursor.execute(
            f"""UPDATE offices SET {', '.join(updates)} 
                WHERE id = %s 
                RETURNING id, office_number, floor, area_sqm, price_per_month, 
                          description, amenities, is_free, created_at""",
            tuple(params)
        )
        
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        conn.commit()
        
        # ✅ Безопасный парсинг JSON
        try:
            amenities_data = json.loads(row['amenities']) if row['amenities'] else None
        except (json.JSONDecodeError, TypeError, Exception):
            amenities_data = None
        
        return OfficeResponse(
            id=row['id'],
            office_number=row['office_number'],
            floor=row['floor'],
            area_sqm=float(row['area_sqm']),
            price_per_month=float(row['price_per_month']),
            description=row['description'] if row['description'] else None,
            amenities=amenities_data,
            is_free=bool(row['is_free']),
            created_at=row['created_at']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.delete("/{office_id}", response_model=dict)
def delete_office(office_id: int, current_user: dict = Depends(get_current_user)):
    """
    Удаление офиса
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        office_id: ID офиса для удаления
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: Сообщение об успешном удалении
    
    Raises:
        HTTPException: 403 если роль не admin/manager
        HTTPException: 404 если офис не найден
        HTTPException: 500 если ошибка при удалении
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM offices WHERE id = %s RETURNING id", (office_id,))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        conn.commit()
        
        return {"message": f"Офис {office_id} удалён"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/stats/summary", response_model=dict)
def get_offices_stats(current_user: dict = Depends(get_current_user)):
    """
    Статистика по офисам
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: Статистика (общее количество, свободные, занятые, средний доход)
    
    Raises:
        HTTPException: 403 если роль не admin/manager
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Общее количество
        cursor.execute("SELECT COUNT(*) as count FROM offices")
        total = cursor.fetchone()['count']
        
        # Свободные
        cursor.execute("SELECT COUNT(*) as count FROM offices WHERE is_free = TRUE")
        free = cursor.fetchone()['count']
        
        # Занятые
        cursor.execute("SELECT COUNT(*) as count FROM offices WHERE is_free = FALSE")
        rented = cursor.fetchone()['count']
        
        # Общий потенциальный доход
        cursor.execute("SELECT COALESCE(SUM(price_per_month), 0) as total FROM offices")
        total_income = cursor.fetchone()['total']
        
        # Средний доход с офиса
        cursor.execute("SELECT COALESCE(AVG(price_per_month), 0) as avg FROM offices")
        avg_income = cursor.fetchone()['avg']
        
        return {
            "total_offices": total,
            "free_offices": free,
            "rented_offices": rented,
            "total_potential_income": float(total_income),
            "average_office_income": round(float(avg_income), 2)
        }
    finally:
        cursor.close()
        conn.close()