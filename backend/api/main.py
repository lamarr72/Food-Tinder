from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from backend.core.exceptions import AppError
from backend.api.feed_router import router as feed_router
from backend.api.auth_router import router as auth_router

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
app.include_router(auth_router)

@app.get("/", tags=["Проверка связи"])
async def root():
    return {"status": "ok", "message": "Сервер Food Tinder успешно работает!"}

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )