# backend/api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from api.config import settings
from datetime import datetime
from api.rate_limiter import limiter, setup_rate_limiting, RATE_LIMITS

app = FastAPI(
    title="Business Center API",
    description="API для системы учета аренды офисов",
    version="0.1.0"
)

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
    auth, users, offices, applications, 
    contracts, payments, office_views, 
    audit, ai_rental_prediction, favorites
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(offices.router)
app.include_router(applications.router)
app.include_router(contracts.router)
app.include_router(payments.router)
app.include_router(office_views.router)
app.include_router(audit.router)
app.include_router(ai_rental_prediction.router)
app.include_router(favorites.router)  # ← ЭТА СТРОКА ОТСУТСТВОВАЛА!

# ==============================================
# HEALTH CHECK
# ==============================================

@app.get("/")
def root():
    return {
        "message": "API работает",
        "docs": "/docs",
        "https": settings.cookie_secure,
        "environment": settings.ENVIRONMENT
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