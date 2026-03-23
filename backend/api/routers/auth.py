from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import OAuth2PasswordBearer
from api.database import get_db
from api.models.user import LoginRequest, Token
from api.security import verify_password, create_token, decode_token, blacklist_token, save_refresh_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@router.post("/api/auth/login", tags=["Auth"])
def login(
    login: str = Body(..., embed=True),
    password: str = Body(..., embed=True)
):
    conn = get_db()
    cursor = conn.cursor()
    
    # Запрос возвращает: (id, login, password_hash, role_id, is_active)
    cursor.execute(
        "SELECT id, login, password_hash, role_id, is_active FROM users WHERE login = %s",
        (login,)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    # user — это кортеж! Используем индексы:
    # user[0] = id
    # user[1] = login
    # user[2] = password_hash
    # user[3] = role_id
    # user[4] = is_active
    
    if not user:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    if not verify_password(password, user[2]):  # ← user[2] = password_hash
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    if not user[4]:  # ← user[4] = is_active
        raise HTTPException(status_code=400, detail="Аккаунт заблокирован")
    
    access = create_token(
        {"sub": str(user[0]), "login": user[1], "role_id": user[3]},
        30
    )
    refresh = create_token(
        {"sub": str(user[0]), "login": user[1]},
        10080
    )
    save_refresh_token(user[0], refresh, 7)
    
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": 1800
    }

@router.get("/api/auth/me", tags=["Auth"])
def get_me(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, login, email, role_id FROM users WHERE id = %s",
        (payload.get("sub"),)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # user = (id, login, email, role_id)
    return {
        "id": user[0],
        "login": user[1],
        "email": user[2],
        "role_id": user[3]
    }

@router.post("/api/auth/logout", tags=["Auth"])
def logout(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if payload:
        blacklist_token(token, 30)
    return {"message": "Выход успешен"}