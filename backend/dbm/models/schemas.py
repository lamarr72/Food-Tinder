from typing import Optional

from pydantic import BaseModel, ConfigDict, RootModel, Field, EmailStr
from datetime import date


class TagsShema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class DishesSchema(BaseModel):
    id: int
    name: str

    price: float
    cooking_time: int
    rating: float

    calories: int
    proteins: int
    fats: int
    carbs: int

    photos: list[str] = []

    tags: list[TagsShema] = []

    model_config = ConfigDict(from_attributes=True)


class DishDetailSchema(DishesSchema):
    """
    карточка при клике, наследует класс DishesSchema
    """
    description: str = Field(..., min_length=1, description="Dish description")
    recipe_steps: list = []
    ingredients: list = []

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
