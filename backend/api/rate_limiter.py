# backend/api/rate_limiter.py

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="memory://",
    strategy="fixed-window",
)

def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"Rate limit exceeded for {request.client.host}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "detail": f"Превышен лимит запросов. {exc.detail}",
            "retry_after": 60  # ← заменили exc.retry_after на 60
        },
        headers={"Retry-After": "60"}
    )

def setup_rate_limiting(app: FastAPI):
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

RATE_LIMITS = {
    "public": "30/minute",
    "login": "10/minute",
    "register": "5/minute",
    "authenticated": "200/minute",
    "read": "300/minute",
    "write": "100/minute",
    "delete": "50/minute",
    "ml_train": "5/hour",
    "ml_predict": "60/minute",
    "admin": "100/minute",
    "audit": "50/minute",
}