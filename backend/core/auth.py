import os
from datetime import datetime, timedelta, timezone
import bcrypt 
import jwt
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from backend.dbm.models.repository import UserManager
from backend.core.exceptions import AuthError

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10800))


class AuthService:
    """
    Класс для передачи данных пользователя из ядра в api
    """

    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def check_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    @staticmethod
    def create_access_token(user_id: int, is_guest: bool) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": str(user_id),
            "is_guest": is_guest,
            "exp": expire,
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> dict:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("Срок действия токена истек", status_code=401) from exc
        except jwt.InvalidTokenError as exc:
            raise AuthError("Неправильный токен авторизации", status_code=401) from exc


    async def authenticate_guest(self, session: AsyncSession, session_id: str) -> str:
        user = await self.user_manager.get_by_session_id(session, session_id)

        if user is None:
            user = await self.user_manager.create_guest(session, session_id)

        is_guest = user.email is None
        return self.create_access_token(user.id, is_guest)

    async def register_user(self, session: AsyncSession, session_id: str,
                            password: str, email: str) -> str:

        existing_user = await self.user_manager.get_by_email(session, email)
        if existing_user is not None: 
            raise AuthError("пользователь с таким email уже существует", status_code=409)

        hashed_password = self.hash_password(password)
        guest_user = await self.user_manager.get_by_session_id(session, session_id)

        if guest_user is not None and guest_user.email is None:
            user = await self.user_manager.attach_credentials(
                session=session,
                user=guest_user,
                email=email,
                hashed_password=hashed_password,
            )
        elif guest_user is None:
            user = await self.user_manager.create_registered_user(
                session=session,
                session_id=session_id,
                email=email,
                hashed_password=hashed_password,
            )
        else:
            user = await self.user_manager.create_registered_user(
                session=session,
                session_id=None,
                email=email,
                hashed_password=hashed_password,
            )    

        return self.create_access_token(user_id=user.id, is_guest=False)

    async def authenticate_user(self, session: AsyncSession, email: str, password: str):

        user = await self.user_manager.get_by_email(session, email)

        if user is None or user.hashed_password is None:
            raise AuthError("Неверный пароль или email", status_code=401)
        
        if not self.check_password(password, user.hashed_password):
            raise AuthError("Неверный пароль или email", status_code=401)

        return self.create_access_token(user_id=user.id, is_guest=False)