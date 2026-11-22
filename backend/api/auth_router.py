from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.dbm.models.schemas import GuestSchema, UserRegisterSchema, UserLoginSchema, TokenResponse
from backend.dbm.database import get_db_session
from backend.core.auth import AuthService
from backend.core.exceptions import AuthError
from backend.dbm.models.repository import UserManager

router = APIRouter(prefix="/auth", tags=["Авторизация и Регистрация"])
user_manager = UserManager()
auth_service = AuthService(user_manager)


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
    token = await auth_service.authenticate_guest(session, request.session_id)
    
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register", response_model=TokenResponse)
async def register_user(
    request: UserRegisterSchema,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Превращение гостя в полноценного пользователя.
    Берем старый session_id, находим профиль и дописываем туда email и хэш пароля.
    """

    token = await auth_service.register_user(
        session=session,
        session_id=request.session_id,
        password=request.password,
        email=str(request.email)
        )

    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
async def login_user(
    request: UserLoginSchema,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Обычный вход по email и паролю для уже зарегистрированных пользователей.
    """

    token = await auth_service.authenticate_user(
        session=session,
        email= str(request.email),
        password=request.password
        )

    
    return {"access_token": token, "token_type": "bearer"}