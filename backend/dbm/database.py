import os
import urllib.parse
from dotenv import load_dotenv
#импорты сессии и движка на асинхронные
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

load_dotenv()

#строка подключения к БД
#формат: postgresql://пользователь:пароль@IP-адрес:порт/имя_базы
raw_password = os.getenv("DB_PASS")
password = urllib.parse.quote_plus(raw_password)

user = os.getenv("DB_USER")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)