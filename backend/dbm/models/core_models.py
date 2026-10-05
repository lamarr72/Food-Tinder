import enum
from datetime import datetime, timezone, date
from sqlalchemy import String, Integer, Float, Text, Boolean, ForeignKey, Table, Column, Date, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

# --- ЭНУМЕРАТОРЫ ---
class ReactionType(enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    FAVORITE = "favorite"

class MealType(enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

# --- ТАБЛИЦЫ-СВЯЗКИ ---
dish_tags = Table(
    "dish_tags",
    Base.metadata, 
    Column("dish_id", ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

dish_ingredients = Table(
    "dish_ingredients",
    Base.metadata,
    Column("dish_id", ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True),
    Column("ingredient_id", ForeignKey("ingredients.id", ondelete="CASCADE"), primary_key=True),
    Column("amount", String(50), nullable=True)
)

user_unwanted_ingredients = Table(
    "user_unwanted_ingredients",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("ingredient_id", ForeignKey("ingredients.id", ondelete="CASCADE"), primary_key=True),
)

# --- ОСНОВНЫЕ МОДЕЛИ ---
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    
    # Новые поля из ТЗ
    name: Mapped[str] = mapped_column(String(50), nullable=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=True)
    height: Mapped[int] = mapped_column(Integer, nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

class Ingredient(Base):
    __tablename__ = "ingredients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

class Dish(Base):
    __tablename__ = "dishes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=True)
    
    calories: Mapped[int] = mapped_column(Integer, nullable=True)
    proteins: Mapped[float] = mapped_column(Float, nullable=True)
    fats: Mapped[float] = mapped_column(Float, nullable=True)
    carbs: Mapped[float] = mapped_column(Float, nullable=True)
    cooking_time: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tags: Mapped[list["Tag"]] = relationship(secondary=dish_tags, lazy="selectin")
    ingredients: Mapped[list["Ingredient"]] = relationship(secondary=dish_ingredients, lazy="selectin")
    images: Mapped[list["DishImage"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    steps: Mapped[list["RecipeStep"]] = relationship(cascade="all, delete-orphan", lazy="selectin")

class DishImage(Base):
    __tablename__ = "dish_images"
    id: Mapped[int] = mapped_column(primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"))
    image_url: Mapped[str] = mapped_column(String(255))

class RecipeStep(Base):
    __tablename__ = "recipe_steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"))
    step_number: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(String(255), nullable=True)

class Swipe(Base):
    __tablename__ = "swipes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"))
    
    reaction: Mapped[ReactionType] = mapped_column(SQLEnum(ReactionType))
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)

class RationItem(Base):
    __tablename__ = "ration_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"))
    meal_type: Mapped[MealType] = mapped_column(SQLEnum(MealType))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# --- КЛАСС МАТВЕЯ (Оставляем без изменений) ---
class UserVector(Base):
    __tablename__ = "user_vector"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    weight: Mapped[float] = mapped_column(Float, default=5.0)