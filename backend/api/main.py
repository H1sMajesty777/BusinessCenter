from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Business Center API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routers import auth, users, offices
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(offices.router)

@app.get("/")
def root():
    return {"message": "API работает", "docs": "/docs"}