import json
from fastapi import APIRouter, HTTPException
from api.database import get_db
from api.models.user import 

router = APIRouter()

def user_to_dict(row): # из БД в словарь
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