from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import date
from api.database import get_db
from api.security import decode_token

router = APIRouter()
security = HTTPBearer(auto_error=False)

class ContractCreate(BaseModel):
    application_id: int
    user_id: int
    office_id: int
    start_date: date
    end_date: date
    total_amount: float

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

@router.post("/api/contracts", status_code=201, tags=["Contracts"])
def create_contract(contract: ContractCreate, current_user: dict = Depends(get_current_user)):
    """
    Создание договора аренды
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO contracts (application_id, user_id, office_id, start_date, end_date, total_amount, status_id) 
           VALUES (%s, %s, %s, %s, %s, %s, 4) RETURNING id""",
        (contract.application_id, contract.user_id, contract.office_id, contract.start_date, contract.end_date, contract.total_amount)
    )
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"id": row[0], "message": "Договор создан"}

@router.get("/api/contracts", tags=["Contracts"])
def get_all_contracts(current_user: dict = Depends(get_current_user)):
    """
    Просмотр всех договоров
    Доступ: Админ/Менеджер
    """
    require_admin_or_manager(current_user)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.user_id, u.login, c.office_id, o.office_number, c.start_date, c.end_date, c.total_amount, c.status_id, s.name 
        FROM contracts c 
        JOIN users u ON c.user_id = u.id 
        JOIN offices o ON c.office_id = o.id 
        JOIN statuses s ON c.status_id = s.id 
        ORDER BY c.start_date DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [{"id": r[0], "user_id": r[1], "user_login": r[2], "office_id": r[3], "office_number": r[4], "start_date": str(r[5]), "end_date": str(r[6]), "total_amount": float(r[7]), "status_id": r[8], "status_name": r[9]} for r in rows]

@router.get("/api/contracts/my", tags=["Contracts"])
def get_my_contracts(current_user: dict = Depends(get_current_user)):
    """
    Просмотр своих договоров
    Доступ: Клиент
    """
    user_id = current_user.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.office_id, o.office_number, c.start_date, c.end_date, c.total_amount, c.status_id, s.name 
        FROM contracts c 
        JOIN offices o ON c.office_id = o.id 
        JOIN statuses s ON c.status_id = s.id 
        WHERE c.user_id = %s 
        ORDER BY c.start_date DESC
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [{"id": r[0], "office_id": r[1], "office_number": r[2], "start_date": str(r[3]), "end_date": str(r[4]), "total_amount": float(r[5]), "status_id": r[6], "status_name": r[7]} for r in rows]