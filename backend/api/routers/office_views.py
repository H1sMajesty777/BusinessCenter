from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db
from api.models.office_view import OfficeViewCreate
from typing import List, Optional

router = APIRouter()

def view_to_dict(row) -> dict:
    return {
        "id": row[0],
        "user_id": row[1],
        "office_id": row[2],
        "viewed_at": str(row[3]),
        "duration_seconds": row[4],
        "is_contacted": row[5]
    }

@router.get("/api/office-views", tags=["Просмотры"])
def get_office_views(office_id: Optional[int] = None, user_id: Optional[int] = None):
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT id, user_id, office_id, viewed_at, duration_seconds, is_contacted FROM office_views WHERE 1=1"
    params = []
    
    if office_id:
        query += " AND office_id = %s"
        params.append(office_id)
    if user_id:
        query += " AND user_id = %s"
        params.append(user_id)
    
    query += " ORDER BY viewed_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [view_to_dict(r) for r in rows]

@router.get("/api/office-views/{view_id}", tags=["Просмотры"])
def get_office_view(view_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, office_id, viewed_at, duration_seconds, is_contacted FROM office_views WHERE id = %s", (view_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Просмотр не найден")
    
    return view_to_dict(row)

@router.post("/api/office-views", status_code=201, tags=["Просмотры"])
def create_office_view(view: OfficeViewCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO office_views (user_id, office_id, duration_seconds, is_contacted) VALUES (%s, %s, %s, %s) RETURNING id",
        (view.user_id, view.office_id, view.duration_seconds, view.is_contacted)
    )
    view_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"id": view_id, "message": "Просмотр записан"}

@router.put("/api/office-views/{view_id}", tags=["Просмотры"])
def update_office_view(view_id: int, is_contacted: bool):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE office_views SET is_contacted = %s WHERE id = %s RETURNING id", (is_contacted, view_id))
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Просмотр не найден")
    
    return {"id": row[0], "message": "Просмотр обновлён"}

@router.delete("/api/office-views/{view_id}", tags=["Просмотры"])
def delete_office_view(view_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM office_views WHERE id = %s RETURNING id", (view_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Просмотр не найден")
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"message": f"Просмотр {view_id} удалён"}