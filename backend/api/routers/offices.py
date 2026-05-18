# -*- coding: utf-8 -*-
"""
Роуты для управления офисами бизнес-центра
CRUD операции для офисов: создание, чтение, обновление, удаление
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import json
from api.database import get_db
from api.security import decode_token
from api.models.office import OfficeCreate, OfficeUpdate, OfficeResponse
from api.rate_limiter import limiter, RATE_LIMITS
# from api.security import get_current_user_from_cookie as get_current_user
from api.security import get_current_user 
from api.models.office_image import OfficeImageResponse
from api.utils.audit_logger import log_insert, log_update, log_delete
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/offices", tags=["Offices"])
# security = HTTPBearer(auto_error=False)


# ===================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ===================================================================

# def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     """
#     Получить текущего пользователя из JWT токена
    
#     Args:
#         credentials: JWT токен из заголовка Authorization
    
#     Returns:
#         dict: Payload токена (sub, role_id, login, etc.)
    
#     Raises:
#         HTTPException: 401 если токена нет или он неверный
#     """
#     if not credentials:
#         raise HTTPException(status_code=401, detail="Нет токена")
    
#     token = credentials.credentials
#     payload = decode_token(token)
    
#     if not payload:
#         raise HTTPException(status_code=401, detail="Неверный токен")
    
#     return payload


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
# ===================================================================
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ML ПРОГНОЗА
# ===================================================================

def get_ml_probability(conn, office_id: int) -> float:
    try:
        from api.ml_models.office_rental_prediction import rental_predictor
        result = rental_predictor.predict_probability(conn, office_id)
        if "error" not in result and "probability" in result:
            return result["probability"]
    except Exception as e:
        logger.warning(f"ML prediction failed for office {office_id}: {e}")
    return None

@router.get("", response_model=List[OfficeResponse])
def get_offices(
    request: Request,
    floor: Optional[int] = Query(None, description="Фильтр по этажу"),
    max_price: Optional[float] = Query(None, description="Максимальная цена"),
    is_free: Optional[bool] = Query(None, description="Только свободные офисы")
):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Основной запрос БЕЗ комментариев
        query = """
            SELECT 
                o.id, o.office_number, o.floor, o.area_sqm, o.price_per_month, 
                o.description, o.amenities, o.is_free, o.created_at,
                COALESCE(
                    (SELECT COUNT(*) FROM office_views 
                    WHERE office_id = o.id AND viewed_at > NOW() - INTERVAL '30 days'), 0
                ) as views_30d,
                COALESCE(
                    (SELECT COUNT(*) FROM applications WHERE office_id = o.id), 0
                ) as applications_count,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'id', img.id,
                            'office_id', img.office_id,           -- ← ДОБАВИТЬ!
                            'image_url', img.image_url,
                            'is_primary', img.is_primary,
                            'sort_order', img.sort_order,
                            'created_at', img.created_at          -- ← ДОБАВИТЬ!
                        )
                    ) FILTER (WHERE img.id IS NOT NULL),
                    '[]'
                ) as images
            FROM offices o
            LEFT JOIN office_images img ON o.id = img.office_id
            WHERE 1=1
        """
        params = []
        
        if floor is not None:
            query += " AND o.floor = %s"
            params.append(floor)
        
        if max_price is not None:
            query += " AND o.price_per_month <= %s"
            params.append(max_price)
        
        if is_free is not None:
            query += " AND o.is_free = %s"
            params.append(is_free)
        
        query += " GROUP BY o.id ORDER BY o.floor, o.office_number"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for r in rows:
            try:
                amenities_data = json.loads(r['amenities']) if r['amenities'] else None
            except:
                amenities_data = None
            
            images_data = []
            if r['images'] and r['images'] != '[]':
                try:
                    images_data = json.loads(r['images']) if isinstance(r['images'], str) else r['images']
                except:
                    images_data = []
            
            ml_prob = get_ml_probability(conn, r['id'])
            
            result.append(OfficeResponse(
                id=r['id'],
                office_number=r['office_number'],
                floor=r['floor'],
                area_sqm=float(r['area_sqm']),
                price_per_month=float(r['price_per_month']),
                description=r['description'] if r['description'] else None,
                amenities=amenities_data,
                is_free=bool(r['is_free']),
                created_at=r['created_at'],
                images=[OfficeImageResponse(**img) for img in images_data],
                views_30d=r.get('views_30d', 0) or 0,
                applications_count=r.get('applications_count', 0) or 0,
                ml_probability=ml_prob
            ))
        
        return result
    except Exception as e:
        logger.error(f"Error in get_offices: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.post("", status_code=201, response_model=OfficeResponse)
@limiter.limit(RATE_LIMITS["authenticated"])
def create_office(request: Request, office: OfficeCreate, current_user: dict = Depends(get_current_user)):
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
        
        # АУДИТ: логируем создание офиса
        log_insert(
            user_id=current_user.get("sub"),
            table_name="offices",
            record_id=row['id'],
            new_values={
                "office_number": row['office_number'],
                "floor": row['floor'],
                "area_sqm": float(row['area_sqm']),
                "price_per_month": float(row['price_per_month']),
                "is_free": row['is_free']
            },
            conn=conn
        )
        
        conn.commit()
        
        try:
            amenities_data = json.loads(row['amenities']) if row['amenities'] else None
        except:
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
    finally:
        cursor.close()
        conn.close()


@router.get("/{office_id}", response_model=OfficeResponse)
def get_office(request: Request, office_id: int):
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
        
        # Безопасный парсинг JSON
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
@limiter.limit(RATE_LIMITS["authenticated"])
def update_office(request: Request, office_id: int, office: OfficeUpdate, current_user: dict = Depends(get_current_user)):
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверяем существование
        cursor.execute("SELECT id FROM offices WHERE id = %s", (office_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        # Собираем только те поля, которые переданы
        update_data = office.model_dump(exclude_none=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")
        
        # Преобразуем amenities в JSON если есть
        if 'amenities' in update_data and update_data['amenities'] is not None:
            update_data['amenities'] = json.dumps(update_data['amenities'], ensure_ascii=False)
        
        # Строим запрос динамически
        updates = []
        params = []
        for key, value in update_data.items():
            updates.append(f"{key} = %s")
            params.append(value)
        
        params.append(office_id)
        
        query = f"""
            UPDATE offices 
            SET {', '.join(updates)} 
            WHERE id = %s 
            RETURNING id, office_number, floor, area_sqm, price_per_month, 
                      description, amenities, is_free, created_at
        """
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.commit()
        
        # Парсим amenities обратно
        amenities_data = None
        if row['amenities']:
            try:
                amenities_data = json.loads(row['amenities'])
            except:
                pass
        
        return OfficeResponse(
            id=row['id'],
            office_number=row['office_number'],
            floor=row['floor'],
            area_sqm=float(row['area_sqm']),
            price_per_month=float(row['price_per_month']),
            description=row['description'],
            amenities=amenities_data,
            is_free=row['is_free'],
            created_at=row['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import sys
        print("=" * 80)
        print("❌ КРИТИЧЕСКАЯ ОШИБКА В UPDATE_OFFICE:")
        print(f"Office ID: {office_id}")
        print(f"Данные для обновления: {update_data if 'update_data' in locals() else 'N/A'}")
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Текст: {str(e)}")
        print("\n📋 ПОЛНЫЙ СТЕК ВЫЗОВОВ:")
        traceback.print_exc(file=sys.stdout)
        print("=" * 80)
        raise HTTPException(status_code=500, detail=f"Ошибка обновления офиса: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def get_office_before_update(conn, office_id: int) -> dict:
    """Получить текущие данные офиса для аудита"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT office_number, floor, area_sqm, price_per_month, is_free, description FROM offices WHERE id = %s",
            (office_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()

@router.delete("/{office_id}", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def delete_office(request: Request, office_id: int, current_user: dict = Depends(get_current_user)):
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
        # Добавьте эту функцию перед её использованием
        # Получаем данные для аудита перед удалением
        old_data = get_office_before_update(conn, office_id)
        if not old_data:
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        cursor.execute("DELETE FROM offices WHERE id = %s RETURNING id", (office_id,))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        # АУДИТ: логируем удаление
        log_delete(
            user_id=current_user.get("sub"),
            table_name="offices",
            record_id=office_id,
            old_values={
                "office_number": old_data['office_number'],
                "floor": old_data['floor'],
                "area_sqm": float(old_data['area_sqm']),
                "price_per_month": float(old_data['price_per_month']),
                "is_free": old_data['is_free']
            },
            conn=conn
        )
        
        conn.commit()
        
        return {"message": f"Офис {office_id} удалён"}
    finally:
        cursor.close()
        conn.close()


@router.get("/stats/summary", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def get_offices_stats(request: Request, current_user: dict = Depends(get_current_user)):
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

@router.post("/{office_id}/track-view")
@limiter.limit(RATE_LIMITS["authenticated"])
def track_office_view(
    request: Request,
    office_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Отслеживание просмотра офиса пользователем
    Доступ: Все авторизованные
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверяем существование офиса
        cursor.execute("SELECT id FROM offices WHERE id = %s", (office_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        # Добавляем запись в office_views
        cursor.execute("""
            INSERT INTO office_views (user_id, office_id, viewed_at)
            VALUES (%s, %s, NOW())
        """, (user_id, office_id))
        
        # ⚠️ УДАЛЯЕМ ЭТОТ БЛОК - колонки views_count нет в таблице!
        # cursor.execute("""
        #     UPDATE offices 
        #     SET views_count = COALESCE(views_count, 0) + 1
        #     WHERE id = %s
        # """, (office_id,))
        
        conn.commit()
        
        return {"message": "Просмотр зафиксирован"}
        
    except Exception as e:
        logger.error(f"Error tracking view: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()