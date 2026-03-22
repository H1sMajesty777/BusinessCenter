from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db
from api.models.contract import ContractCreate
from typing import List, Optional

router = APIRouter()

def contract_to_dict(row) -> dict:
    return {
        "id": row[0],
        "application_id": row[1],
        "user_id": row[2],
        "office_id": row[3],
        "start_date": str(row[4]),
        "end_date": str(row[5]),
        "total_amount": float(row[6]),
        "status_id": row[7],
        "signed_at": str(row[8]) if row[8] else None
    }

@router.get("/api/contracts", tags=["Договоры"])
def get_contracts(user_id: Optional[int] = None, status_id: Optional[int] = None):
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT id, application_id, user_id, office_id, start_date, end_date, total_amount, status_id, signed_at FROM contracts WHERE 1=1"
    params = []
    
    if user_id:
        query += " AND user_id = %s"
        params.append(user_id)
    if status_id:
        query += " AND status_id = %s"
        params.append(status_id)
    
    query += " ORDER BY signed_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [contract_to_dict(r) for r in rows]

@router.get("/api/contracts/{contract_id}", tags=["Договоры"])
def get_contract(contract_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, application_id, user_id, office_id, start_date, end_date, total_amount, status_id, signed_at FROM contracts WHERE id = %s", (contract_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Договор не найден")
    
    return contract_to_dict(row)

@router.post("/api/contracts", status_code=201, tags=["Договоры"])
def create_contract(contract: ContractCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO contracts (application_id, user_id, office_id, start_date, end_date, total_amount, status_id) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (contract.application_id, contract.user_id, contract.office_id, contract.start_date, contract.end_date, contract.total_amount, contract.status_id)
    )
    contract_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"id": contract_id, "message": "Договор создан"}

@router.put("/api/contracts/{contract_id}", tags=["Договоры"])
def update_contract(contract_id: int, status_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE contracts SET status_id = %s WHERE id = %s RETURNING id", (status_id, contract_id))
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Договор не найден")
    
    return {"id": row[0], "message": "Договор обновлён"}

@router.delete("/api/contracts/{contract_id}", tags=["Договоры"])
def delete_contract(contract_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contracts WHERE id = %s RETURNING id", (contract_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Договор не найден")
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"message": f"Договор {contract_id} удалён"}