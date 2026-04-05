# -*- coding: utf-8 -*-
"""
Роуты для управления платежами
Учёт платежей за аренду офисов: создание, просмотр, статистика
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import date, datetime
from api.database import get_db
from api.security import decode_token
from api.models.payment import PaymentCreate, PaymentUpdate, PaymentResponse
from api.rate_limiter import limiter, RATE_LIMITS

# Router с правильным префиксом
router = APIRouter(prefix="/api/payments", tags=["Payments"])
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
def create_payment(request: Request, payment: PaymentCreate = Body(...), current_user: dict = Depends(get_current_user)):
    """
    Создание платежа
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        payment: Данные платежа (contract_id, amount, payment_date, status_id)
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: ID созданного платежа и сообщение
    
    Raises:
        HTTPException: 404 если договор не найден
        HTTPException: 403 если роль не admin/manager
        HTTPException: 500 если ошибка при создании
    
    Note:
        payment_date устанавливается автоматически если не передана
        status_id=9 по умолчанию (оплачено)
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка что договор существует
        cursor.execute("SELECT id FROM contracts WHERE id = %s", (payment.contract_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Договор не найден")
        
        # Если дата не передана — используем сегодня
        payment_date = payment.payment_date if payment.payment_date else date.today()
        
        # Создание платежа
        cursor.execute(
            """INSERT INTO payments (contract_id, amount, payment_date, status_id, transaction_id) 
               VALUES (%s, %s, %s, %s, %s) RETURNING id, payment_date""",
            (payment.contract_id, payment.amount, payment_date, payment.status_id, payment.transaction_id)
        )
        row = cursor.fetchone()
        conn.commit()
        
        return {
            "id": row['id'], 
            "message": "Платёж создан", 
            "amount": payment.amount,
            "payment_date": str(row['payment_date'])
        }
    
    finally:
        cursor.close()
        conn.close()


@router.get("", response_model=List[dict])
@limiter.limit(RATE_LIMITS["authenticated"])
def get_all_payments(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: dict = Depends(get_current_user)
):
    """
    Просмотр всех платежей
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Returns:
        List[dict]: Список всех платежей с данными договоров и пользователей
    
    Raises:
        HTTPException: 403 если роль не admin/manager
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT p.id, p.contract_id, c.user_id, u.login, p.amount, 
                   p.payment_date, p.status_id, s.name, p.transaction_id, p.created_at 
            FROM payments p 
            JOIN contracts c ON p.contract_id = c.id 
            JOIN users u ON c.user_id = u.id 
            JOIN statuses s ON p.status_id = s.id 
            ORDER BY p.payment_date DESC
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        
        return [
            {
                "id": r['id'],
                "contract_id": r['contract_id'],
                "user_id": r['user_id'],
                "user_login": r['login'],
                "amount": float(r['amount']),
                "payment_date": str(r['payment_date']),
                "status_id": r['status_id'],
                "status_name": r['name'],
                "transaction_id": r['transaction_id'],
                "created_at": str(r['created_at']) if r['created_at'] else None
            }
            for r in rows
        ]
    
    finally:
        cursor.close()
        conn.close()


@router.get("/my", response_model=List[dict])
@limiter.limit(RATE_LIMITS["authenticated"])
def get_my_payments(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Просмотр своих платежей
    
    Доступ: Все авторизованные (клиент видит только свои)
    
    Args:
        current_user: Текущий пользователь из токена
    
    Returns:
        List[dict]: Список платежей текущего пользователя
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT p.id, p.contract_id, p.amount, p.payment_date, 
                   p.status_id, s.name, p.transaction_id 
            FROM payments p 
            JOIN contracts c ON p.contract_id = c.id 
            JOIN statuses s ON p.status_id = s.id 
            WHERE c.user_id = %s 
            ORDER BY p.payment_date DESC
        """, (user_id,))
        rows = cursor.fetchall()
        
        return [
            {
                "id": r['id'],
                "contract_id": r['contract_id'],
                "amount": float(r['amount']),
                "payment_date": str(r['payment_date']),
                "status_id": r['status_id'],
                "status_name": r['name'],
                "transaction_id": r['transaction_id']
            }
            for r in rows
        ]
    
    finally:
        cursor.close()
        conn.close()


@router.get("/{payment_id}", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def get_payment(request: Request, payment_id: int, current_user: dict = Depends(get_current_user)):
    """
    Просмотр конкретного платежа по ID
    
    Доступ: Админ/Менеджер или владелец платежа
    
    Args:
        payment_id: ID платежа
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: Данные платежа
    
    Raises:
        HTTPException: 404 если платёж не найден
        HTTPException: 403 если нет доступа к платежу
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT p.id, p.contract_id, c.user_id, u.login, p.amount, 
                   p.payment_date, p.status_id, s.name, p.transaction_id, p.created_at 
            FROM payments p 
            JOIN contracts c ON p.contract_id = c.id 
            JOIN users u ON c.user_id = u.id 
            JOIN statuses s ON p.status_id = s.id 
            WHERE p.id = %s
        """, (payment_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Платёж не найден")
        
        # Проверка прав доступа (админ/менеджер или владелец)
        if current_user.get("role_id") not in [1, 2]:
            if str(current_user.get("sub")) != str(row['user_id']):
                raise HTTPException(status_code=403, detail="Нет доступа к платежу")
        
        return {
            "id": row['id'],
            "contract_id": row['contract_id'],
            "user_id": row['user_id'],
            "user_login": row['login'],
            "amount": float(row['amount']),
            "payment_date": str(row['payment_date']),
            "status_id": row['status_id'],
            "status_name": row['name'],
            "transaction_id": row['transaction_id'],
            "created_at": str(row['created_at']) if row['created_at'] else None
        }
    
    finally:
        cursor.close()
        conn.close()


@router.put("/{payment_id}", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def update_payment(
    request: Request,
    payment_id: int,
    payment_update: PaymentUpdate = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Обновление платежа
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        payment_id: ID платежа
        payment_update: Новые данные платежа
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: Сообщение об успешном обновлении
    
    Raises:
        HTTPException: 400 если нет данных для обновления
        HTTPException: 403 если роль не admin/manager
        HTTPException: 404 если платёж не найден
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if payment_update.amount is not None:
            updates.append("amount = %s")
            params.append(payment_update.amount)
        
        if payment_update.payment_date is not None:
            updates.append("payment_date = %s")
            params.append(payment_update.payment_date)
        
        if payment_update.status_id is not None:
            updates.append("status_id = %s")
            params.append(payment_update.status_id)
        
        if payment_update.transaction_id is not None:
            updates.append("transaction_id = %s")
            params.append(payment_update.transaction_id)
        
        if not updates:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")
        
        params.append(payment_id)
        
        cursor.execute(
            f"UPDATE payments SET {', '.join(updates)} WHERE id = %s RETURNING id",
            tuple(params)
        )
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Платёж не найден")
        
        conn.commit()
        
        return {"message": f"Платёж {payment_id} обновлён"}
    
    finally:
        cursor.close()
        conn.close()


@router.delete("/{payment_id}", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def delete_payment(request: Request, payment_id: int, current_user: dict = Depends(get_current_user)):
    """
    Удаление платежа
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        payment_id: ID платежа
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: Сообщение об успешном удалении
    
    Raises:
        HTTPException: 403 если роль не admin/manager
        HTTPException: 404 если платёж не найден
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM payments WHERE id = %s RETURNING id", (payment_id,))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Платёж не найден")
        
        conn.commit()
        
        return {"message": f"Платёж {payment_id} удалён"}
    
    finally:
        cursor.close()
        conn.close()


@router.get("/stats", response_model=dict)
@limiter.limit(RATE_LIMITS["authenticated"])
def get_payment_stats(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Статистика платежей
    
    Доступ: Админ/Менеджер (role_id 1 или 2)
    
    Args:
        current_user: Текущий пользователь из токена
    
    Returns:
        dict: Статистика по платежам (сумма, количество, по месяцам)
    
    Raises:
        HTTPException: 403 если роль не admin/manager
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Общая сумма всех платежей
        cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM payments")
        total_amount = cursor.fetchone()['total']
        
        # Количество платежей
        cursor.execute("SELECT COUNT(*) as count FROM payments")
        total_count = cursor.fetchone()['count']
        
        # Платежи за текущий месяц
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count 
            FROM payments 
            WHERE EXTRACT(MONTH FROM payment_date) = EXTRACT(MONTH FROM CURRENT_DATE)
            AND EXTRACT(YEAR FROM payment_date) = EXTRACT(YEAR FROM CURRENT_DATE)
        """)
        month_row = cursor.fetchone()
        month_amount = month_row['total']
        month_count = month_row['count']
        
        # Платежи по статусам
        cursor.execute("""
            SELECT s.name, COUNT(p.id) as count, COALESCE(SUM(p.amount), 0) as total
            FROM payments p
            JOIN statuses s ON p.status_id = s.id
            GROUP BY s.name
            ORDER BY total DESC
        """)
        by_status = cursor.fetchall()
        
        # Топ договоров по сумме платежей
        cursor.execute("""
            SELECT c.id, u.login, SUM(p.amount) as total
            FROM payments p
            JOIN contracts c ON p.contract_id = c.id
            JOIN users u ON c.user_id = u.id
            GROUP BY c.id, u.login
            ORDER BY total DESC
            LIMIT 5
        """)
        top_contracts = cursor.fetchall()
        
        return {
            "total_amount": float(total_amount),
            "total_count": total_count,
            "current_month": {
                "amount": float(month_amount),
                "count": month_count
            },
            "by_status": [
                {"status_name": r['name'], "count": r['count'], "total_amount": float(r['total'])}
                for r in by_status
            ],
            "top_contracts": [
                {"contract_id": r['id'], "user_login": r['login'], "total_amount": float(r['total'])}
                for r in top_contracts
            ]
        }
    
    finally:
        cursor.close()
        conn.close()


@router.get("/contract/{contract_id}", response_model=List[dict])
@limiter.limit(RATE_LIMITS["authenticated"])
def get_contract_payments(
    request: Request,
    contract_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Просмотр всех платежей по конкретному договору
    
    Доступ: Админ/Менеджер или владелец договора
    
    Args:
        contract_id: ID договора
        current_user: Текущий пользователь из токена
    
    Returns:
        List[dict]: Список платежей указанного договора
    
    Raises:
        HTTPException: 404 если договор не найден
        HTTPException: 403 если нет доступа
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка что договор существует и получение user_id
        cursor.execute("SELECT user_id FROM contracts WHERE id = %s", (contract_id,))
        contract = cursor.fetchone()
        
        if not contract:
            raise HTTPException(status_code=404, detail="Договор не найден")
        
        # Проверка прав доступа
        if current_user.get("role_id") not in [1, 2]:
            if str(current_user.get("sub")) != str(contract['user_id']):
                raise HTTPException(status_code=403, detail="Нет доступа к платежам этого договора")
        
        cursor.execute("""
            SELECT p.id, p.amount, p.payment_date, p.status_id, s.name, p.transaction_id 
            FROM payments p 
            JOIN statuses s ON p.status_id = s.id 
            WHERE p.contract_id = %s 
            ORDER BY p.payment_date DESC
        """, (contract_id,))
        rows = cursor.fetchall()
        
        return [
            {
                "id": r['id'],
                "amount": float(r['amount']),
                "payment_date": str(r['payment_date']),
                "status_id": r['status_id'],
                "status_name": r['name'],
                "transaction_id": r['transaction_id']
            }
            for r in rows
        ]
    
    finally:
        cursor.close()
        conn.close()