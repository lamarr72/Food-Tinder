import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.dbm.models.base import Base
from backend.dbm.database import get_db_session
from backend.api.main import app
from backend.dbm.models.core_models import (
    User, Tag, Ingredient, Dish, DishImage, RecipeStep,
    dish_tags, dish_ingredients, MealType, ReactionType
)

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def seed_dishes(db_session: AsyncSession):
    """Наполняет тестовую БД начальными блюдами с тегами и ингредиентами через insert"""
    # 1. Теги
    tag_breakfast = Tag(name="Завтрак")
    tag_meat = Tag(name="Мясо")
    tag_fish = Tag(name="Рыба")
    tag_high_protein = Tag(name="Высокий белок")
    db_session.add_all([tag_breakfast, tag_meat, tag_fish, tag_high_protein])

    # 2. Ингредиенты
    ingr_egg = Ingredient(name="Яйцо куриное")
    ingr_beef = Ingredient(name="Говядина")
    ingr_salmon = Ingredient(name="Лосось")
    ingr_peanut = Ingredient(name="Арахис")
    db_session.add_all([ingr_egg, ingr_beef, ingr_salmon, ingr_peanut])
    await db_session.flush()

    # 3. Блюда
    dish_scramble = Dish(
        name="Скрэмбл",
        description="Нежный завтрак",
        price=150,
        calories=300,
        proteins=18.0,
        fats=20.0,
        carbs=2.0,
        cooking_time=10,
        rating=4.9,
        is_public=True
    )
    dish_steak = Dish(
        name="Стейк из говядины",
        description="Сочный стейк",
        price=600,
        calories=550,
        proteins=45.0,
        fats=35.0,
        carbs=0.0,
        cooking_time=20,
        rating=5.0,
        is_public=True
    )
    dish_salmon = Dish(
        name="Запеченный лосось",
        description="Свежая рыба",
        price=500,
        calories=400,
        proteins=35.0,
        fats=25.0,
        carbs=1.0,
        cooking_time=25,
        rating=4.8,
        is_public=True
    )
    db_session.add_all([dish_scramble, dish_steak, dish_salmon])
    await db_session.flush()

    # Связи тегов через таблицу-связку dish_tags
    await db_session.execute(insert(dish_tags).values([
        {"dish_id": dish_scramble.id, "tag_id": tag_breakfast.id},
        {"dish_id": dish_scramble.id, "tag_id": tag_high_protein.id},
        {"dish_id": dish_steak.id, "tag_id": tag_meat.id},
        {"dish_id": dish_steak.id, "tag_id": tag_high_protein.id},
        {"dish_id": dish_salmon.id, "tag_id": tag_fish.id},
        {"dish_id": dish_salmon.id, "tag_id": tag_high_protein.id},
    ]))

    # Связи ингредиентов через dish_ingredients (с quantity и unit)
    await db_session.execute(insert(dish_ingredients).values([
        {"dish_id": dish_scramble.id, "ingredient_id": ingr_egg.id, "quantity": 3.0, "unit": "шт"},
        {"dish_id": dish_steak.id, "ingredient_id": ingr_beef.id, "quantity": 250.0, "unit": "г"},
        {"dish_id": dish_salmon.id, "ingredient_id": ingr_salmon.id, "quantity": 200.0, "unit": "г"},
    ]))

    await db_session.commit()

    return {
        "tags": {
            "breakfast": tag_breakfast,
            "meat": tag_meat,
            "fish": tag_fish,
            "high_protein": tag_high_protein
        },
        "ingredients": {
            "egg": ingr_egg,
            "beef": ingr_beef,
            "salmon": ingr_salmon,
            "peanut": ingr_peanut
        },
        "dishes": {
            "scramble": dish_scramble,
            "steak": dish_steak,
            "salmon": dish_salmon
        }
    }
