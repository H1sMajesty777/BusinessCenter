from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Business Center API",
    description="API для системы учета аренды офисов",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routers import auth, users, offices, applications, contracts, payments, office_views, audit

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(offices.router)
app.include_router(applications.router)
app.include_router(contracts.router)
app.include_router(payments.router)
app.include_router(office_views.router)
app.include_router(audit.router)

@app.get("/")
def root():
    return {"message": "API работает", "docs": "/docs"}