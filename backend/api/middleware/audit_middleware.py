# backend/api/middleware/audit_middleware.py
# -*- coding: utf-8 -*-
"""
Middleware для автоматического логирования всех изменений в БД
"""

import json
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from api.database import get_db
from api.security import get_current_user_optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware для аудита всех запросов POST, PUT, PATCH, DELETE
    """
    
    async def dispatch(self, request: Request, call_next):
        # Пропускаем GET и OPTIONS запросы
        if request.method in ["GET", "OPTIONS", "HEAD"]:
            return await call_next(request)
        
        # Получаем пользователя (опционально, может быть None)
        user_payload = await get_current_user_optional(request)
        user_id = user_payload.get("sub") if user_payload else None
        user_login = user_payload.get("login") if user_payload else "anonymous"
        
        # Логируем запрос
        logger.info(f"AUDIT: {request.method} {request.url.path} by user {user_login} (id:{user_id})")
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Для DELETE запросов - сразу логируем
        if request.method == "DELETE":
            await self._log_delete_action(request, user_id, user_login, response)
        
        return response
    
    async def _log_delete_action(self, request: Request, user_id: int, user_login: str, response):
        """Логирование DELETE операций"""
        # Извлекаем ID из пути (например, /api/users/5)
        path_parts = request.url.path.split("/")
        table_name = path_parts[2] if len(path_parts) > 2 else "unknown"
        record_id = None
        
        for part in path_parts:
            if part.isdigit():
                record_id = int(part)
                break
        
        if response.status_code == 200 and record_id:
            conn = get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO audit_log (user_id, action_type, table_name, record_id, old_values, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    "DELETE",
                    table_name,
                    record_id,
                    json.dumps({"deleted_id": record_id}, ensure_ascii=False),
                    datetime.now()
                ))
                conn.commit()
                logger.info(f"AUDIT LOG: DELETE on {table_name}/{record_id} by {user_login}")
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
            finally:
                cursor.close()
                conn.close()