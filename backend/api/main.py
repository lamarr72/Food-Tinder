from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.feed_router import router as feed_router

app = FastAPI(
    title="Food Tinder API",
    description="Бэкенд сервиса персональных рекомендаций рецептов",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # На этапе разработки разрешаем запросы со всех адресов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем GET, POST, PUT, DELETE и т.д.
    allow_headers=["*"],
)

app.include_router(feed_router)

@app.get("/", tags=["Проверка связи"])
async def root():
    return {"status": "ok", "message": "Сервер Food Tinder успешно работает!"}