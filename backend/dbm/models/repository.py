from datetime import datetime, timezone
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from .core_models import (
    Dish, Swipe, Ingredient, Tag, UserVector,
    user_unwanted_ingredients, dish_ingredients, ReactionType
)
from .schemas import DishesSchema, UserVectorSchema


class DishManager:
    """
    класс отвечающий за перевод информации из БД в ядро.
    с помощью pydantic валидирует и приводит данные в вид, понятный ядру
    """

    async def get_candidate_dishes(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 200,
        tag_name: str | None = None,
        max_cooking_time: int | None = None
    ) -> list[dict]:
        """
        берет из таблицы dishes блюда, которые еще не видел пользователь,
        и отправляет их ядру в виде списка словарей
        """
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # дизлайк скрывает блюдо только до конца дня, остальные реакции — насовсем
        swipes_query = select(Swipe.dish_id).where(
            Swipe.user_id == user_id,
            or_(
                Swipe.reaction != ReactionType.DISLIKE,
                Swipe.created_at >= today_start
            )
        )
        result = await session.execute(swipes_query)
        swipes_id_list = [row[0] for row in result.all()]

        unwanted_query = (
            select(user_unwanted_ingredients.c.ingredient_id)
            .where(user_unwanted_ingredients.c.user_id == user_id)
        )
        unwanted_result = await session.execute(unwanted_query)
        unwanted_ids = [row[0] for row in unwanted_result.all()]

        query = (
            select(Dish)
            .options(
                selectinload(Dish.tags),
                selectinload(Dish.images),
                selectinload(Dish.steps)
            )
            .where(Dish.is_public == True)
        )

        if swipes_id_list:
            query = query.where(Dish.id.notin_(swipes_id_list))

        if unwanted_ids:
            query = query.where(~Dish.ingredients.any(Ingredient.id.in_(unwanted_ids)))

        if tag_name:
            query = query.where(Dish.tags.any(Tag.name == tag_name))

        if max_cooking_time is not None:
            query = query.where(Dish.cooking_time <= max_cooking_time)

        query = query.limit(limit)

        result = await session.execute(query)
        dishes = result.scalars().all()

        if not dishes:
            return []

        # отдельно подтягиваем ингредиенты с количеством и единицами измерения из связки
        dish_ids = [dish.id for dish in dishes]
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
        for row in ingr_result.all():
            ingr_by_dish[row.dish_id].append({
                "id": row.id,
                "name": row.name,
                "quantity": row.quantity,
                "unit": row.unit
            })

        candidates_dishes = []
        for dish in dishes:
            dish_pydantic = DishesSchema.model_validate({
                "id": dish.id,
                "name": dish.name,
                "description": dish.description,
                "price": dish.price,
                "calories": dish.calories,
                "proteins": dish.proteins,
                "fats": dish.fats,
                "carbs": dish.carbs,
                "cooking_time": dish.cooking_time,
                "difficulty": dish.difficulty,
                "equipment": dish.equipment,
                "rating": dish.rating,
                "tags": dish.tags,
                "images": dish.images,
                "steps": sorted(dish.steps, key=lambda s: s.step_number),
                "ingredients": ingr_by_dish.get(dish.id, [])
            })
            candidates_dishes.append(dish_pydantic.model_dump())

        return candidates_dishes

    async def get_user_vector(self, session: AsyncSession, user_id: int):
        """
        отправляет вектор пользователя ядру, в виде словаря {мясо : 8}
        """
        query = (
            select(Tag.name, UserVector.weight)
            .join(Tag, Tag.id == UserVector.tag_id)
            .where(UserVector.user_id == user_id)
        )

        result = await session.execute(query)
        raw_vector = {row.name: row.weight for row in result.all()}
        valid_vector = UserVectorSchema.model_validate(raw_vector)

        return valid_vector

    async def save_swipe(
        self,
        session: AsyncSession,
        m_dish_id: int,
        m_user_id: int,
        m_reaction: ReactionType
    ):
        """
        Сохраняет свайп конкретного пользователя, со всеми данными, был ли лайкнут,
        и тп.
        """
        query = Swipe(
            user_id=m_user_id,
            dish_id=m_dish_id,
            reaction=m_reaction,
            is_processed=False
        )
        session.add(query)
        await session.commit()
        return True

    async def count_unprocessed_swipes(self, session: AsyncSession, user_id: int):
        query = (
            select(func.count()).select_from(Swipe)
            .where(
                Swipe.user_id == user_id,
                Swipe.is_processed == False
            )
        )
        result = await session.execute(query)
        return result.scalar_one()

    async def process_vector_batch(self, session: AsyncSession, user_id: int):
        query = (
            select(Swipe)
            .where(Swipe.user_id == user_id, Swipe.is_processed == False)
            .options(selectinload(Swipe.dish).selectinload(Dish.tags))
        )
        result = await session.execute(query)
        unprocessed_swipes = result.scalars().all()

        if not unprocessed_swipes:
            return

        tag_deltas = {}
        for swipe in unprocessed_swipes:
            if swipe.reaction == ReactionType.FAVORITE:
                delta = 2.0
            elif swipe.reaction == ReactionType.LIKE:
                delta = 1.0
            else:
                delta = -0.5

            for tag in swipe.dish.tags:
                tag_deltas[tag.id] = tag_deltas.get(tag.id, 0.0) + delta

        query = (
            select(UserVector)
            .where(
                UserVector.user_id == user_id,
                UserVector.tag_id.in_(tag_deltas.keys())
            )
        )
        result = await session.execute(query)

        user_vector = {uv.tag_id: uv for uv in result.scalars().all()}

        for tag_id, delta in tag_deltas.items():
            if tag_id in user_vector:
                user_vector[tag_id].weight += delta
            else:
                new_vector_item = UserVector(
                    user_id=user_id,
                    tag_id=tag_id,
                    weight=5.0 + delta
                )
                session.add(new_vector_item)

        for swipe in unprocessed_swipes:
            swipe.is_processed = True

        await session.commit()