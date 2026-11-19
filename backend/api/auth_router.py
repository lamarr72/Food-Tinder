from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.dbm.models.schemas import GuestSchema, UserRegisterSchema, UserLoginSchema, TokenResponse
from backend.dbm.database import get_db_session

router = APIRouter(prefix="/auth", tags=["Авторизация и Регистрация"])


@router.post("/guest", response_model=TokenResponse)
async def login_or_create_guest(
    request: GuestSchema,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Вход для гостя.
    Фронтенд присылает session_id, мы ищем гостя в базе (или создаем нового)
    и возвращаем JWT-токен для автоматического входа.
    """
    # ЗАГЛУШКА: Скоро здесь будет вызов auth_service.authenticate_guest(...)
    return {"access_token": f"guest_token_for_{request.session_id}", "token_type": "bearer"}


@router.post("/register", response_model=TokenResponse)
async def register_user(
    request: UserRegisterSchema,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Превращение гостя в полноценного пользователя.
    Берем старый session_id, находим профиль и дописываем туда email и хэш пароля.
    """
    # ЗАГЛУШКА: Скоро здесь будет вызов auth_service.register_user(...)
    return {"access_token": f"user_token_for_{request.email}", "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
async def login_user(
    request: UserLoginSchema,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Обычный вход по email и паролю для уже зарегистрированных пользователей.
    """
    # ЗАГЛУШКА: Скоро здесь будет вызов auth_service.authenticate_user(...)
    return {"access_token": "real_jwt_token_here", "token_type": "bearer"}