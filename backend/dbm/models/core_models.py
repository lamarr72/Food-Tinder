from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Text, Boolean, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

"""
Файл со всеми таблицами и их атрибутами в БД
"""

# Промежуточная таблица для свзяи блюд и тегов
dish_tags = Table(
    "dish_tags",
    Base.metadata, 
    Column("dish_id", ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

# Таблица пользователей
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

# Таблица тегов
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

# Расширенная таблица блюд
class Dish(Base):
    __tablename__ = "dishes"

    #базовая информация
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str] = mapped_column(String(255), nullable=True)

    #КБЖУ
    calories: Mapped[int] = mapped_column(Integer, nullable=True)
    proteins: Mapped[float] = mapped_column(Float, nullable=True)
    fats: Mapped[float] = mapped_column(Float, nullable=True)
    carbs: Mapped[float] = mapped_column(Float, nullable=True)

    #контент
    ingredients: Mapped[str] = mapped_column(Text, nullable=True)
    recipe: Mapped[str] = mapped_column(Text, nullable=True)

    #системные поля (UGX и модерация)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    #Если мы берем теги у блюда, с помощью relationship
    #мы сразу берем все зависимости из таблицы dish_tags
    tags: Mapped[list["Tag"]] = relationship(secondary=dish_tags, lazy="selectin")

# Таблица свайпов
class Swipe(Base):
    __tablename__ = "swipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"))
    is_liked: Mapped[bool] = mapped_column(Boolean)

    #нужно для проверки, учитывался ли этот свайп для пересчета вектора
    is_processed: Mapped[bool] = mapped_column(Boolean)

# ТАблица сохраненного рациона
class RationItem(Base):
    __tablename__ = "ration_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"))
    added_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

# Таблица для вектора пользователя
class UserVector(Base):
    __tablename__ = "user_vector"

    #адресс строки будет состоять из комбинации ID пользователя + ключ, так гарантируется что
    #связка имя пользователя + "мясо"(к примеру), будет встречаться только раз в таблице
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    weight: Mapped[Float] = mapped_column(Float, deafult=5.0)
    





