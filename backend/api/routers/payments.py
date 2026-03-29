from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import date
from api.database import get_db
from api.security import decode_token

router = APIRouter()
security = HTTPBearer(auto_error=False)

class PaymentCreate(BaseModel):
    contract_id: int
    amount: float
    status_id: int = 11  # paid

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Нет токена")
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    return payload

def require_admin_or_manager(current_user: dict):
    if current_user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Только админ и менеджер")

@router.post("/api/payments", status_code=201, tags=["Payments"])
def create_payment(payment: PaymentCreate, current_user: dict = Depends(get_current_user)):
    """
    Учет платежей (создание)
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO payments (contract_id, amount, payment_date, status_id) 
           VALUES (%s, %s, %s, %s) RETURNING id""",
        (payment.contract_id, payment.amount, date.today(), payment.status_id)
    )
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"id": row[0], "message": "Платёж создан"}

@router.get("/api/payments", tags=["Payments"])
def get_all_payments(current_user: dict = Depends(get_current_user)):
    """
    Учет платежей (просмотр всех)
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.contract_id, c.user_id, u.login, p.amount, p.payment_date, p.status_id, s.name 
        FROM payments p 
        JOIN contracts c ON p.contract_id = c.id 
        JOIN users u ON c.user_id = u.id 
        JOIN statuses s ON p.status_id = s.id 
        ORDER BY p.payment_date DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [{"id": r[0], "contract_id": r[1], "user_id": r[2], "user_login": r[3], "amount": float(r[4]), "payment_date": str(r[5]), "status_id": r[6], "status_name": r[7]} for r in rows]

@router.get("/api/payments/my", tags=["Payments"])
def get_my_payments(current_user: dict = Depends(get_current_user)):
    """
    Учет платежей (просмотр своих)
    Доступ: Клиент
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.contract_id, p.amount, p.payment_date, p.status_id, s.name 
        FROM payments p 
        JOIN contracts c ON p.contract_id = c.id 
        JOIN statuses s ON p.status_id = s.id 
        WHERE c.user_id = %s 
        ORDER BY p.payment_date DESC
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [{"id": r[0], "contract_id": r[1], "amount": float(r[2]), "payment_date": str(r[3]), "status_id": r[4], "status_name": r[5]} for r in rows]