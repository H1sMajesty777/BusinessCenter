# backend/api/main.py
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from api.config import settings
from datetime import datetime
from api.rate_limiter import limiter, setup_rate_limiting, RATE_LIMITS
import os

# ==============================================
# СОЗДАНИЕ ПРИЛОЖЕНИЯ
# ==============================================

app = FastAPI(
    title="Business Center API",
    description="API для системы учета аренды офисов",
    version="0.1.0"
)

# ==============================================
# СТАТИЧЕСКИЕ ФАЙЛЫ (ДЛЯ ЗАГРУЖЕННЫХ ИЗОБРАЖЕНИЙ)
# ==============================================

uploads_dir = "uploads"
os.makedirs(uploads_dir, exist_ok=True)
os.makedirs("uploads/offices", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
print("Static files mounted: /uploads")

# ==============================================
# RATE LIMITING
# ==============================================

setup_rate_limiting(app)

# ==============================================
# MIDDLEWARE
# ==============================================

if settings.BEHIND_PROXY:
    from fastapi.middleware.proxy import ProxyHeadersMiddleware
    app.add_middleware(
        ProxyHeadersMiddleware,
        trusted_hosts=["*"],
    )
    print("Proxy headers middleware enabled")

if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1"]
    )
    print("Trusted host middleware enabled")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
print("CORS middleware configured (HttpOnly Cookie ready)")

# ==============================================
# РОУТЕРЫ
# ==============================================

from api.routers import (
    auth,
    users,
    offices,
    office_images,
    applications,
    contracts,
    payments,
    office_views,
    audit,
    ai_rental_prediction,
    favorites,
    admin  # ← ДОБАВИТЬ ЭТУ СТРОКУ
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(offices.router)
app.include_router(office_images.router)
app.include_router(applications.router)
app.include_router(contracts.router)
app.include_router(payments.router)
app.include_router(office_views.router)
app.include_router(audit.router)
app.include_router(ai_rental_prediction.router)
app.include_router(favorites.router)
app.include_router(admin.router)  # ← ДОБАВИТЬ ЭТУ СТРОКУ

print("=" * 60)
print("ROUTERS REGISTERED:")
print("  - /api/auth")
print("  - /api/users")
print("  - /api/offices")
print("  - /api/office-images")
print("  - /api/applications")
print("  - /api/contracts")
print("  - /api/payments")
print("  - /api/office-views")
print("  - /api/audit")
print("  - /api/ai/rental-prediction")
print("  - /api/favorites")
print("  - /api/admin          ← ADMIN ROUTES")
print("=" * 60)

# ==============================================
# HEALTH CHECK
# ==============================================

@app.get("/")
def root():
    return {
        "message": "Business Center API работает",
        "docs": "/docs",
        "https": settings.cookie_secure,
        "environment": settings.ENVIRONMENT,
        "static_files": "/uploads"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "business-center-api",
        "auth": "HttpOnly Cookie",
        "https": settings.cookie_secure,
        "secure_cookies": settings.cookie_secure,
        "behind_proxy": settings.BEHIND_PROXY,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )