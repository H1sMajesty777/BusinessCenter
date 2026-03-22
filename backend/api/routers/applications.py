from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db
from api.models.application import ApplicationCreate
from typing import List, Optional
from datetime import datetime

router = APIRouter()

def app_to_dict(row) -> dict:
    return {
        "id": row[0],
        "user_id": row[1],
        "office_id": row[2],
        "status_id": row[3],
        "comment": row[4],
        "created_at": str(row[5]) if row[5] else None,
        "reviewed_at": str(row[6]) if row[6] else None
    }

@router.get("/api/applications", tags=["Заявки"])
def get_applications(status_id: Optional[int] = None, user_id: Optional[int] = None):
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT id, user_id, office_id, status_id, comment, created_at, reviewed_at FROM applications WHERE 1=1"
    params = []
    
    if status_id:
        query += " AND status_id = %s"
        params.append(status_id)
    if user_id:
        query += " AND user_id = %s"
        params.append(user_id)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [app_to_dict(r) for r in rows]

@router.get("/api/applications/{app_id}", tags=["Заявки"])
def get_application(app_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, office_id, status_id, comment, created_at, reviewed_at FROM applications WHERE id = %s", (app_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    return app_to_dict(row)

@router.post("/api/applications", status_code=201, tags=["Заявки"])
def create_application(app: ApplicationCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO applications (user_id, office_id, status_id, comment) VALUES (%s, %s, %s, %s) RETURNING id",
        (app.user_id, app.office_id, app.status_id, app.comment)
    )
    app_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"id": app_id, "message": "Заявка создана"}

@router.put("/api/applications/{app_id}", tags=["Заявки"])
def update_application(app_id: int, status_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE applications SET status_id = %s, reviewed_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id",
        (status_id, app_id)
    )
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    return {"id": row[0], "message": "Заявка обновлена"}

@router.delete("/api/applications/{app_id}", tags=["Заявки"])
def delete_application(app_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM applications WHERE id = %s RETURNING id", (app_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"message": f"Заявка {app_id} удалена"}