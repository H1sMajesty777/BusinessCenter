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
from api.utils.audit_logger import log_insert, log_update, log_delete


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
def create_contract(request: Request, contract: ContractCreate, current_user: dict = Depends(get_current_user)):
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка заявки
        cursor.execute("SELECT id, status_id FROM applications WHERE id = %s", (contract.application_id,))
        app = cursor.fetchone()
        if not app:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        
        if app['status_id'] != 2:
            raise HTTPException(status_code=400, detail="Заявка должна быть одобрена перед созданием договора")
        
        # Проверка офиса
        cursor.execute("SELECT id, is_free, price_per_month FROM offices WHERE id = %s", (contract.office_id,))
        office = cursor.fetchone()
        if not office:
            raise HTTPException(status_code=404, detail="Офис не найден")
        
        if not office['is_free']:
            raise HTTPException(status_code=400, detail="Офис уже арендован")
        
        # Создание договора
        cursor.execute("""
            INSERT INTO contracts (application_id, user_id, office_id, start_date, end_date, total_amount, status_id, signed_at)
            VALUES (%s, %s, %s, %s, %s, %s, 4, NOW())
            RETURNING id, start_date, end_date
        """, (
            contract.application_id,
            contract.user_id,
            contract.office_id,
            contract.start_date,
            contract.end_date,
            contract.total_amount
        ))
        
        result = cursor.fetchone()
        contract_id = result['id']
        start_date = result['start_date']
        end_date = result['end_date']
        
        # ========== АВТОМАТИЧЕСКОЕ СОЗДАНИЕ ПЛАТЕЖЕЙ ==========
        monthly_amount = contract.monthly_amount if contract.monthly_amount else office['price_per_month']
        
        # Генерируем все месяцы между start_date и end_date
        current_date = start_date
        payment_number = 1
        
        while current_date <= end_date:
            cursor.execute("""
                INSERT INTO payments (contract_id, amount, payment_date, status_id, payment_number, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                contract_id,
                monthly_amount,
                current_date,
                9,  # status_id = 9 (ожидает оплаты)
                payment_number,
                f"Арендная плата за {current_date.strftime('%B %Y')}"
            ))
            
            # Переходим к следующему месяцу
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
            payment_number += 1
        
        # Обновляем статус заявки
        cursor.execute("""
            UPDATE applications 
            SET status_id = 4, reviewed_at = NOW() 
            WHERE id = %s
        """, (contract.application_id,))
        
        # Обновляем статус офиса
        cursor.execute("""
            UPDATE offices SET is_free = FALSE WHERE id = %s
        """, (contract.office_id,))
        
        conn.commit()
        
        return {
            "id": contract_id,
            "message": "Договор успешно создан",
            "payments_created": payment_number - 1,
            "monthly_amount": monthly_amount,
            "application_status": "updated",
            "office_status": "rented"
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