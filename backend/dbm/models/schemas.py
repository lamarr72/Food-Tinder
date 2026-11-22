from typing import Optional

from pydantic import BaseModel, ConfigDict, RootModel, Field, EmailStr
from datetime import date
from backend.dbm.models.core_models import ReactionType


class TagSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class DishImageSchema(BaseModel):
    id: int
    image_url: str

    model_config = ConfigDict(from_attributes=True)


class RecipeStepSchema(BaseModel):
    step_number: int
    description: str
    image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DishIngredientSchema(BaseModel):
    id: int
    name: str
    quantity: float
    unit: str


class DishesSchema(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: int | None = None
    calories: int | None = None
    proteins: float | None = None
    fats: float | None = None
    carbs: float | None = None
    cooking_time: int = 0
    difficulty: int = 1
    equipment: str | None = None
    rating: float = 0.0

    tags: list[TagSchema] = []
    images: list[DishImageSchema] = []
    steps: list[RecipeStepSchema] = []
    ingredients: list[DishIngredientSchema] = []

    model_config = ConfigDict(from_attributes=True)


class UserVectorSchema(RootModel[dict[str, float]]):
    pass


# СХЕМЫ АВТОРИЗАЦИИ

class GuestSchema(BaseModel):
    """
    Схема для первого входа гостя по ID устройства
    """

    session_id: str = Field(..., min_length=10, description="Session id")


class UserRegisterSchema(BaseModel):
    """Схема регистрации (привязка почты к гостевому профилю)"""

    email: EmailStr = Field(..., min_length=1, max_length=50, description="Email address")
    password: str = Field(..., min_length=6, max_length=20, description="Password of user")
    session_id: str = Field(..., min_length=10, max_length=50, description="Session id")


class UserLoginSchema(BaseModel):
    """
    Схема для обычного входа по почте и паролю
    """

    email: EmailStr
    password: str


# СХЕМЫ ПРОФИЛЯ

class UserProfileUpdateSchema(BaseModel):
    """
    Схема для редактирования профиля.
    Все поля Optional (необязательные), чтобы фронтенд мог прислать, к примеру,
    только измененный вес, не отправляя заново имя и рост.
    """

    name: Optional[str] = Field(None, max_length=50)
    birth_date: Optional[date] = Field(None, description="Birth date")
    height: Optional[int] = Field(None, description="Height of the user", ge=100, le=250)
    weight: Optional[float] = Field(None, description="Weight of the user", ge=30.0, le=300.0)


class UserProfileResponse(BaseModel):
    """
    Схема для отдачи профиля на фронтенд
    """
    id: int
    email: Optional[EmailStr]
    session_id: Optional[str]
    name: Optional[str]
    birth_date: Optional[date]
    height: Optional[int]
    weight: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class SwipeRequest(BaseModel):
    """
    Схема для POST-запроса.
    Если фронтенд пришлет reaction="super_like", FastAPI автоматически
    выдаст ошибку 422, так как такого значения нет в ReactionType.
    """
    user_id: int
    dish_id: int
    reaction: ReactionType


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
