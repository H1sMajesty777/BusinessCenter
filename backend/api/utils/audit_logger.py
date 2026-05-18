# backend/api/utils/audit_logger.py
# -*- coding: utf-8 -*-
"""
Утилита для записи действий в журнал аудита
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from api.database import get_db

logger = logging.getLogger(__name__)


def log_action(
    user_id: Optional[int],
    action_type: str,
    table_name: str,
    record_id: Optional[int] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    conn = None
):
    """
    Запись действия в журнал аудита
    
    Args:
        user_id: ID пользователя (может быть None для системных действий)
        action_type: Тип действия (INSERT, UPDATE, DELETE, LOGIN, LOGOUT)
        table_name: Имя таблицы
        record_id: ID записи
        old_values: Старые значения
        new_values: Новые значения
        conn: Существующее соединение с БД (опционально)
    """
    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True
    
    cursor = conn.cursor()
    
    try:
        # Преобразуем old_values в JSON
        old_json = json.dumps(old_values, ensure_ascii=False, default=str) if old_values else None
        
        # Преобразуем new_values в JSON
        new_json = json.dumps(new_values, ensure_ascii=False, default=str) if new_values else None
        
        cursor.execute("""
            INSERT INTO audit_log (user_id, action_type, table_name, record_id, old_values, new_values, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            action_type,
            table_name,
            record_id,
            old_json,
            new_json,
            datetime.now()
        ))
        
        conn.commit()
        logger.debug(f"Audit log: {action_type} on {table_name}/{record_id} by user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
    finally:
        cursor.close()
        if should_close:
            conn.close()


def log_insert(user_id: int, table_name: str, record_id: int, new_values: Dict[str, Any], conn=None):
    """Логирование INSERT операции"""
    log_action(user_id, "INSERT", table_name, record_id, None, new_values, conn)


def log_update(user_id: int, table_name: str, record_id: int, old_values: Dict[str, Any], new_values: Dict[str, Any], conn=None):
    """Логирование UPDATE операции"""
    log_action(user_id, "UPDATE", table_name, record_id, old_values, new_values, conn)


def log_delete(user_id: int, table_name: str, record_id: int, old_values: Dict[str, Any], conn=None):
    """Логирование DELETE операции"""
    log_action(user_id, "DELETE", table_name, record_id, old_values, None, conn)


def log_login(user_id: int, success: bool, conn=None):
    """Логирование попытки входа"""
    log_action(
        user_id if success else None,
        "LOGIN_SUCCESS" if success else "LOGIN_FAILED",
        "auth",
        None,
        {"success": success},
        {"user_id": user_id} if success else {"attempt": "failed"},
        conn
    )


def log_logout(user_id: int, conn=None):
    """Логирование выхода"""
    log_action(user_id, "LOGOUT", "auth", None, None, {"logged_out": True}, conn)