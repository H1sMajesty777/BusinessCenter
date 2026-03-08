import json
from fastapi import APIRouter, HTTPException
from api.database import get_db
from api.models.office import OfficeCreate, OfficeUpdate

router = APIRouter()

def office_to_dict(row):
    """Конвертирует строку из БД в словарь"""
    return {
        'id': row[0], 
        'office_number': row[1], 
        'floor': row[2],
        'area_sqm': float(row[3]), 
        'price_per_month': float(row[4]),
        'description': row[5], 
        'amenities': row[6], 
        'status_id': row[7]
    }

@router.get('/api/offices', tags=['Офисы'])
def get_offices(floor: int = None, max_price: float = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM offices ORDER BY price_per_month')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [office_to_dict(r) for r in rows]

@router.post('/api/offices', status_code=201)
def create_office(office: OfficeCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO offices (office_number, floor, area_sqm, price_per_month, description, amenities, status_id) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id, office_number",
        (office.office_number, office.floor, office.area_sqm, office.price_per_month, office.description, 
         json.dumps(office.amenities) if office.amenities else None, office.status_id)
    )
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return {'id': row[0], 'office_number': row[1], 'message': 'Офис создан'}

@router.get('/api/offices/{office_id}')
def get_office(office_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM offices WHERE id = %s', (office_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail='Офис не найден')
    return office_to_dict(row)

@router.put('/api/offices/{office_id}')
def update_office(office_id: int, office: OfficeUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    data = office.model_dump(exclude_unset=True)
    if not data:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail='Нет данных для обновления')
    
    if 'amenities' in data and data['amenities']:
        data['amenities'] = json.dumps(data['amenities'])
    
    set_clause = ', '.join(f'{k} = %s' for k in data.keys())
    values = list(data.values()) + [office_id]
    
    cursor.execute(f'UPDATE offices SET {set_clause} WHERE id = %s RETURNING id, office_number', values)
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail='Офис не найден')
    
    return {'id': row[0], 'office_number': row[1], 'message': 'Офис обновлён'}

@router.delete('/api/offices/{office_id}')
def delete_office(office_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM offices WHERE id = %s RETURNING id', (office_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail='Офис не найден')
    conn.commit()
    cursor.close()
    conn.close()
    return {'message': f'Офис {office_id} удалён'}