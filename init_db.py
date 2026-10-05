import asyncio
from backend.dbm.database import engine
from backend.dbm.models.base import Base
# Импортируем ВСЕ классы, чтобы SQLAlchemy их увидела
from backend.dbm.models.core_models import (
    User, Tag, Dish, Swipe, RationItem, UserVector,
    dish_tags, Ingredient, DishImage, RecipeStep,
    dish_ingredients, user_unwanted_ingredients
)

async def create_tables():
    print("Connecting to DB and recreating tables (Async mode)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("The tables were successfully created!")

if __name__ == "__main__":
    asyncio.run(create_tables())