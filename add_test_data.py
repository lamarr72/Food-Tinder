import asyncio
from datetime import date
from sqlalchemy import insert
from backend.dbm.database import SessionLocal
from backend.dbm.models.core_models import (
    User, Tag, Ingredient, Dish, DishImage, RecipeStep, Swipe, RationItem,
    dish_tags, dish_ingredients, user_unwanted_ingredients,
    ReactionType, MealType
)

async def add_test_data():
    async with SessionLocal() as db:
        try:
            # 1. Тестовый пользователь Ирина
            new_user = User(
                email="irina@test.ru",
                session_id="session_irina_001",
                name="Ирина",
                birth_date=date(2002, 2, 16),
                height=170,
                weight=65.0
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            # 2. Ингредиенты
            ingr_egg = Ingredient(name="Яйцо куриное")
            ingr_peach = Ingredient(name="Персик")
            ingr_strawberry = Ingredient(name="Клубника")
            ingr_butter = Ingredient(name="Сливочное масло")
            db.add_all([ingr_egg, ingr_peach, ingr_strawberry, ingr_butter])
            await db.commit()
            
            # 3. Аллергии (через execute)
            await db.execute(insert(user_unwanted_ingredients).values([
                {"user_id": new_user.id, "ingredient_id": ingr_peach.id},
                {"user_id": new_user.id, "ingredient_id": ingr_strawberry.id},
                {"user_id": new_user.id, "ingredient_id": ingr_egg.id}
            ]))

            # 4. Теги и блюдо
            tag_breakfast = Tag(name="Завтрак")
            db.add(tag_breakfast)
            await db.commit()

            scramble = Dish(
                name="Идеальный скрэмбл",
                description="Нежные, кремовые яйца на сливочном масле.",
                calories=318, proteins=21.0, fats=24.0, carbs=2.0,
                cooking_time=15, rating=5.0,
                author_id=new_user.id,
                is_public=True
            )
            db.add(scramble)
            await db.commit()
            await db.refresh(scramble)

            # 5. Связи блюда
            await db.execute(insert(dish_tags).values([{"dish_id": scramble.id, "tag_id": tag_breakfast.id}]))
            await db.execute(insert(dish_ingredients).values([
                {"dish_id": scramble.id, "ingredient_id": ingr_egg.id, "amount": "3 шт"},
                {"dish_id": scramble.id, "ingredient_id": ingr_butter.id, "amount": "15 г"}
            ]))
            
            # 6. Фото и шаги
            photo1 = DishImage(dish_id=scramble.id, image_url="/static/images/scramble_1.jpg")
            photo2 = DishImage(dish_id=scramble.id, image_url="/static/images/scramble_2.jpg")
            db.add_all([photo1, photo2])

            step1 = RecipeStep(dish_id=scramble.id, step_number=1, description="Слегка взбить яйца.", image_url="/static/images/step_1.jpg")
            step2 = RecipeStep(dish_id=scramble.id, step_number=2, description="Растопить масло на слабом огне.", image_url=None)
            db.add_all([step1, step2])
            
            # 7. Реакции и рацион
            favorite_swipe = Swipe(user_id=new_user.id, dish_id=scramble.id, reaction=ReactionType.FAVORITE)
            ration = RationItem(user_id=new_user.id, dish_id=scramble.id, meal_type=MealType.BREAKFAST)
            db.add_all([favorite_swipe, ration])
            
            await db.commit()
            print("The test profile and recipe have been added to the database.")
            
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(add_test_data())