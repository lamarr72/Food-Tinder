from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession 
from .schemas import UserVectorSchema, DishesSchema
from core_models import Dish, Tag, Swipe, UserVector

class DishManager:
    """
    класс отвечающий за перевод инофрмации из БД в ядро.
    с помощью pydantic валидирует и приводит данные в вид, понятный ядру
    """

    async def get_candidate_dishes(self, session: AsyncSession,
                                   user_id: int, limit: int = 20) -> list[dict]:
        query = (
                    select(Swipe)
                    .where(Swipe.user_id == user_id)
        )
        result = await session.execute(query)
        swipes_id_list = [row[0] for row in result.all()]

        query = (select(Dish).options(selectinload(Dish.tags)))

        if swipes_id_list:
            query = query.where(Dish.id not in swipes_id_list)

        result = await session.execute(query)
        dishes = result.scalars().all()

        candidates_dishes = []
        for dish in dishes:
            dish_pydantic = DishesSchema.model_validate(dish)
            candidates_dishes.append(dish_pydantic.model_dump())

        return candidates_dishes






    pass

    async def get_user_vector(self, session: AsyncSession, user_id,):

        query = (
                    select(Tag.name, UserVector.weight)
                    .join(Tag, Tag.id == UserVector.tag_id)
                    .where(UserVector.user_id == user_id)
        )

        result = await session.execute(query)
        raw_vector = {row.name: row.weight for row in result.all()}
        valid_vector = UserVectorSchema.model_validate(raw_vector)

        return valid_vector


    async def save_swipe():
        return
    