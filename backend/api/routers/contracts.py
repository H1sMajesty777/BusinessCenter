from fastapi import APIRouter, HTTPException, Depends, Body, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import date, datetime
from api.database import get_db
from api.security import decode_token
from api.models.contract import ContractCreate, ContractResponse
from api.rate_limiter import limiter, RATE_LIMITS
# from api.security import get_current_user_from_cookie as get_current_user
from api.security import get_current_user 


router = APIRouter(prefix="/api/contracts", tags=["Contracts"])
# security = HTTPBearer(auto_error=False)


# def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     """
#     Получить текущего пользователя из JWT токена
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
    """
    if current_user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Только админ и менеджер")


# ENDPOINTS

@router.post("", status_code=201, response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def create_contract(request: Request, contract: ContractCreate = Body(...), current_user: dict = Depends(get_current_user)):
    """
    Создание договора аренды
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка что заявка существует
        cursor.execute("SELECT id FROM applications WHERE id = %s", (contract.application_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        
        # Проверка что офис существует
        cursor.execute("SELECT id FROM offices WHERE id = %s", (contract.office_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        # Проверка что пользователь существует
        cursor.execute("SELECT id FROM users WHERE id = %s", (contract.user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Создание договора (status_id=4 = действует)
        cursor.execute(
            """INSERT INTO contracts (application_id, user_id, office_id, start_date, end_date, total_amount, status_id) 
               VALUES (%s, %s, %s, %s, %s, %s, 4) RETURNING id, signed_at""",
            (contract.application_id, contract.user_id, contract.office_id, 
             contract.start_date, contract.end_date, contract.total_amount)
        )
        row = cursor.fetchone()
        
        # Обновляем статус заявки на "одобрено" (status_id=2)
        cursor.execute("UPDATE applications SET status_id = 2, reviewed_at = %s WHERE id = %s", 
                      (datetime.now(), contract.application_id))
        
        # Обновляем статус офиса на "сдан" (is_free=False)
        cursor.execute("UPDATE offices SET is_free = FALSE WHERE id = %s", (contract.office_id,))
        
        conn.commit()
        
        return {
            "id": row['id'], 
            "message": "Договор создан", 
            "status": "действует",
            "signed_at": str(row['signed_at']) if row['signed_at'] else None
        }
    
    finally:
        cursor.close()
        conn.close()


@router.get("", response_model=List[dict])
@limiter.limit(RATE_LIMITS["authenticated"])
def get_all_contracts(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Просмотр всех договоров
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT c.id, c.application_id, c.user_id, u.login, c.office_id, o.office_number, 
                   c.start_date, c.end_date, c.total_amount, c.status_id, s.name, c.signed_at 
            FROM contracts c 
            JOIN users u ON c.user_id = u.id 
            JOIN offices o ON c.office_id = o.id 
            JOIN statuses s ON c.status_id = s.id 
            ORDER BY c.start_date DESC
        """)
        rows = cursor.fetchall()
        
        return [
            {
                "id": r['id'],
                "application_id": r['application_id'],
                "user_id": r['user_id'],
                "user_login": r['login'],
                "office_id": r['office_id'],
                "office_number": r['office_number'],
                "start_date": str(r['start_date']),
                "end_date": str(r['end_date']),
                "total_amount": float(r['total_amount']),
                "status_id": r['status_id'],
                "status_name": r['name'],
                "signed_at": str(r['signed_at']) if r['signed_at'] else None
            }
            for r in rows
        ]
    
    finally:
        cursor.close()
        conn.close()


@router.get("/my", response_model=List[dict])
@limiter.limit(RATE_LIMITS["authenticated"])
def get_my_contracts(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Просмотр своих договоров
    Доступ: Все авторизованные (клиент видит только свои)
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT c.id, c.application_id, c.office_id, o.office_number, 
                   c.start_date, c.end_date, c.total_amount, c.status_id, s.name, c.signed_at 
            FROM contracts c 
            JOIN offices o ON c.office_id = o.id 
            JOIN statuses s ON c.status_id = s.id 
            WHERE c.user_id = %s 
            ORDER BY c.start_date DESC
        """, (user_id,))
        rows = cursor.fetchall()
        
        return [
            {
                "id": r['id'],
                "application_id": r['application_id'],
                "office_id": r['office_id'],
                "office_number": r['office_number'],
                "start_date": str(r['start_date']),
                "end_date": str(r['end_date']),
                "total_amount": float(r['total_amount']),
                "status_id": r['status_id'],
                "status_name": r['name'],
                "signed_at": str(r['signed_at']) if r['signed_at'] else None
            }
            for r in rows
        ]
    
    finally:
        cursor.close()
        conn.close()


@router.get("/{contract_id}", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def get_contract(request: Request, contract_id: int, current_user: dict = Depends(get_current_user)):
    """
    Просмотр конкретного договора по ID
    Доступ: Админ/Менеджер или владелец договора
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT c.id, c.application_id, c.user_id, u.login, c.office_id, o.office_number, 
                   c.start_date, c.end_date, c.total_amount, c.status_id, s.name, c.signed_at 
            FROM contracts c 
            JOIN users u ON c.user_id = u.id 
            JOIN offices o ON c.office_id = o.id 
            JOIN statuses s ON c.status_id = s.id 
            WHERE c.id = %s
        """, (contract_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Договор не найден")
        
        # Проверка прав доступа (админ/менеджер или владелец)
        if current_user.get("role_id") not in [1, 2]:
            if str(current_user.get("sub")) != str(row['user_id']):
                raise HTTPException(status_code=403, detail="Нет доступа к договору")
        
        return {
            "id": row['id'],
            "application_id": row['application_id'],
            "user_id": row['user_id'],
            "user_login": row['login'],
            "office_id": row['office_id'],
            "office_number": row['office_number'],
            "start_date": str(row['start_date']),
            "end_date": str(row['end_date']),
            "total_amount": float(row['total_amount']),
            "status_id": row['status_id'],
            "status_name": row['name'],
            "signed_at": str(row['signed_at']) if row['signed_at'] else None
        }
    
    finally:
        cursor.close()
        conn.close()


@router.put("/{contract_id}/status", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def update_contract_status(
    request: Request,
    contract_id: int, 
    status_id: int = Body(..., embed=True),
    current_user: dict = Depends(get_current_user)
):
    """
    Изменение статуса договора
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE contracts SET status_id = %s WHERE id = %s RETURNING id",
            (status_id, contract_id)
        )
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Договор не найден")
        
        conn.commit()
        
        return {"message": f"Статус договора {contract_id} обновлён", "new_status_id": status_id}
    
    finally:
        cursor.close()
        conn.close()


@router.delete("/{contract_id}", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def delete_contract(request: Request, contract_id: int, current_user: dict = Depends(get_current_user)):
    """
    Удаление договора
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM contracts WHERE id = %s RETURNING id", (contract_id,))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Договор не найден")
        
        conn.commit()
        
        return {"message": f"Договор {contract_id} удалён"}
    
    finally:
        cursor.close()
        conn.close()