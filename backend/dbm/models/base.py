from sqlalchemy.orm import DeclarativeBase

#все будущие таблицы будут наследоваться от этого класса
class Base(DeclarativeBase):
    pass