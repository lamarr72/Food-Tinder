# все для работы с таблицей ration_items и выборки избранных/лайкнутых блюд для автоподбора.
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from .core_models import (
    RationItem, Dish, Swipe, Ingredient,
    dish_ingredients, MealType, ReactionType
)


class RationManager:
    """
    работа с рационом пользователя в БД
    """

    async def get_ration_items(self, session: AsyncSession, user_id: int) -> list[dict]:
        """
        возвращает все позиции рациона пользователя вместе с данными блюд и ингредиентами
        """
        query = (
            select(RationItem, Dish)
            .join(Dish, Dish.id == RationItem.dish_id)
            .options(selectinload(Dish.tags))
            .where(RationItem.user_id == user_id)
            .order_by(RationItem.day_number, RationItem.id)
        )
        result = await session.execute(query)
        rows = result.all()

        if not rows:
            return []

        dish_ids = list({dish.id for _, dish in rows})
        ingr_by_dish = {d_id: [] for d_id in dish_ids}

        ingr_query = (
            select(
                dish_ingredients.c.dish_id,
                Ingredient.id,
                Ingredient.name,
                dish_ingredients.c.quantity,
                dish_ingredients.c.unit
            )
            .join(Ingredient, Ingredient.id == dish_ingredients.c.ingredient_id)
            .where(dish_ingredients.c.dish_id.in_(dish_ids))
        )
        ingr_result = await session.execute(ingr_query)
        for r in ingr_result.all():
            ingr_by_dish[r.dish_id].append({
                "id": r.id,
                "name": r.name,
                "quantity": r.quantity,
                "unit": r.unit
            })

        items = []
        for item, dish in rows:
            items.append({
                "id": item.id,
                "day_number": item.day_number,
                "meal_type": item.meal_type.value,
                "portion_grams": item.portion_grams,
                "dish": {
                    "id": dish.id,
                    "name": dish.name,
                    "price": dish.price or 0,
                    "calories": dish.calories or 0,
                    "proteins": dish.proteins or 0.0,
                    "fats": dish.fats or 0.0,
                    "carbs": dish.carbs or 0.0,
                    "cooking_time": dish.cooking_time,
                    "tags": [t.name for t in dish.tags],
                    "ingredients": ingr_by_dish.get(dish.id, [])
                }
            })

        return items

    async def add_ration_item(
        self,
        session: AsyncSession,
        user_id: int,
        dish_id: int,
        meal_type: MealType,
        day_number: int = 1,
        portion_grams: int = 100
    ) -> int:
        item = RationItem(
            user_id=user_id,
            dish_id=dish_id,
            meal_type=meal_type,
            day_number=day_number,
            portion_grams=portion_grams
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item.id

    async def update_ration_item(
        self,
        session: AsyncSession,
        item_id: int,
        user_id: int,
        portion_grams: int | None = None,
        day_number: int | None = None,
        meal_type: MealType | None = None
    ) -> bool:
        query = select(RationItem).where(
            RationItem.id == item_id,
            RationItem.user_id == user_id
        )
        result = await session.execute(query)
        item = result.scalar_one_or_none()

        if not item:
            return False

        if portion_grams is not None:
            item.portion_grams = portion_grams
        if day_number is not None:
            item.day_number = day_number
        if meal_type is not None:
            item.meal_type = meal_type

        await session.commit()
        return True

    async def delete_ration_item(self, session: AsyncSession, item_id: int, user_id: int) -> bool:
        query = delete(RationItem).where(
            RationItem.id == item_id,
            RationItem.user_id == user_id
        )
        result = await session.execute(query)
        await session.commit()
        return result.rowcount > 0

    async def clear_ration(self, session: AsyncSession, user_id: int) -> None:
        query = delete(RationItem).where(RationItem.user_id == user_id)
        await session.execute(query)
        await session.commit()

    async def get_favorite_dishes(self, session: AsyncSession, user_id: int) -> list[dict]:
        """
        берет избранные (и если их мало, лайкнутые) блюда пользователя для автоподбора
        """
        query = (
            select(Dish)
            .join(Swipe, Swipe.dish_id == Dish.id)
            .options(selectinload(Dish.tags))
            .where(
                Swipe.user_id == user_id,
                Swipe.reaction.in_([ReactionType.FAVORITE, ReactionType.LIKE])
            )
            .distinct()
        )
        result = await session.execute(query)
        dishes = result.scalars().all()

        return [
            {
                "id": d.id,
                "name": d.name,
                "tags": [t.name for t in d.tags]
            }
            for d in dishes
        ]