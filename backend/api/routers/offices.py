# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import json
from api.database import get_db
from api.security import decode_token
from api.models.office import OfficeCreate, OfficeUpdate, OfficeResponse

router = APIRouter(prefix="/api/offices", tags=["Offices"])
security = HTTPBearer(auto_error=False)


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


@router.get("", response_model=List[OfficeResponse])
def get_offices(
    floor: Optional[int] = Query(None),
    max_price: Optional[float] = Query(None),
    is_free: Optional[bool] = Query(None)
):
    """Каталог офисов — Все (чтение)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT id, office_number, floor, area_sqm, price_per_month, 
                   description, amenities, is_free 
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
            params.append(True if is_free else False)
        
        query += " ORDER BY floor, office_number"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for r in rows:
            # ✅ Безопасный парсинг JSON
            try:
                amenities_data = json.loads(r[6]) if r[6] else None
            except (json.JSONDecodeError, TypeError, Exception):
                amenities_data = None
            
            result.append(
                OfficeResponse(
                    id=int(r[0]),
                    office_number=str(r[1]),
                    floor=int(r[2]),
                    area_sqm=float(r[3]),
                    price_per_month=float(r[4]),
                    description=r[5] if r[5] else None,
                    amenities=amenities_data,
                    is_free=bool(r[7])
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
    """Создание офиса — Админ/Менеджер"""
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO offices (office_number, floor, area_sqm, price_per_month, 
                                   description, amenities, is_free) 
               VALUES (%s, %s, %s, %s, %s, %s, %s) 
               RETURNING id, office_number, floor, area_sqm, price_per_month, 
                         description, amenities, is_free""",
            (
                office.office_number,
                office.floor,
                office.area_sqm,
                office.price_per_month,
                office.description,
                json.dumps(office.amenities) if office.amenities else None,
                office.is_free
            )
        )
        row = cursor.fetchone()
        conn.commit()
        
        # ✅ Безопасный парсинг JSON
        try:
            amenities_data = json.loads(row[6]) if row[6] else None
        except (json.JSONDecodeError, TypeError, Exception):
            amenities_data = None
        
        return OfficeResponse(
            id=int(row[0]),
            office_number=str(row[1]),
            floor=int(row[2]),
            area_sqm=float(row[3]),
            price_per_month=float(row[4]),
            description=row[5] if row[5] else None,
            amenities=amenities_data,
            is_free=bool(row[7])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/{office_id}", response_model=OfficeResponse)
def get_office(office_id: int):
    """Офис по ID — Все (чтение)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """SELECT id, office_number, floor, area_sqm, price_per_month, 
                      description, amenities, is_free 
               FROM offices WHERE id = %s""",
            (office_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        # ✅ Безопасный парсинг JSON
        try:
            amenities_data = json.loads(row[6]) if row[6] else None
        except (json.JSONDecodeError, TypeError, Exception):
            amenities_data = None
        
        return OfficeResponse(
            id=int(row[0]),
            office_number=str(row[1]),
            floor=int(row[2]),
            area_sqm=float(row[3]),
            price_per_month=float(row[4]),
            description=row[5] if row[5] else None,
            amenities=amenities_data,
            is_free=bool(row[7])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.put("/{office_id}", response_model=OfficeResponse)
def update_office(office_id: int, office: OfficeUpdate, current_user: dict = Depends(get_current_user)):
    """Обновление офиса — Админ/Менеджер"""
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
            params.append(json.dumps(office.amenities))
        
        if office.is_free is not None:
            updates.append("is_free = %s")
            params.append(True if office.is_free else False)
        
        if not updates:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")
        
        params.append(office_id)
        
        cursor.execute(
            f"""UPDATE offices SET {', '.join(updates)} 
                WHERE id = %s 
                RETURNING id, office_number, floor, area_sqm, price_per_month, 
                          description, amenities, is_free""",
            tuple(params)
        )
        
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        conn.commit()
        
        # ✅ Безопасный парсинг JSON
        try:
            amenities_data = json.loads(row[6]) if row[6] else None
        except (json.JSONDecodeError, TypeError, Exception):
            amenities_data = None
        
        return OfficeResponse(
            id=int(row[0]),
            office_number=str(row[1]),
            floor=int(row[2]),
            area_sqm=float(row[3]),
            price_per_month=float(row[4]),
            description=row[5] if row[5] else None,
            amenities=amenities_data,
            is_free=bool(row[7])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.delete("/{office_id}")
def delete_office(office_id: int, current_user: dict = Depends(get_current_user)):
    """Удаление офиса — Админ/Менеджер"""
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