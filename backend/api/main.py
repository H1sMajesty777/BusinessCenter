from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='Business Center API')

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Подключаем роутеры
from api.routers import offices
app.include_router(offices.router)

@app.get('/')
def root():
    return {'message': 'Business Center API', 'docs': '/docs'}