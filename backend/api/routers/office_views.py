from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from api.database import get_db
from api.security import decode_token

router = APIRouter()
security = HTTPBearer(auto_error=False)

class OfficeViewCreate(BaseModel):
    office_id: int
    duration_seconds: Optional[int] = None
    is_contacted: bool = False

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Нет токена")
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    return payload

@router.post("/api/office-views", status_code=201, tags=["OfficeViews"])
def create_office_view(view: OfficeViewCreate, current_user: dict = Depends(get_current_user)):
    """Запись просмотра офиса"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO office_views (user_id, office_id, viewed_at, duration_seconds, is_contacted) 
           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
        (current_user.get("sub"), view.office_id, datetime.now(), view.duration_seconds, view.is_contacted)
    )
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"id": row[0], "message": "Просмотр записан"}