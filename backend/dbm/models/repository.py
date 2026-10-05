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
        """
        берет из таблицы dishes блюда, которые еще не видел пользователь,
        и отправляет их ядру в виде списка сллварей
        """
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

    async def get_user_vector(self, session: AsyncSession, user_id,):
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


    async def save_swipe(self, session: AsyncSession, m_dish_id, m_user_id, m_is_liked):
        """
        Сохраняет свайп конкретного пользователя, со всеми данными, был ли лайкнут,
        и тп.
        """

        query = Swipe(
            user_id = m_user_id,
            dish_id = m_dish_id,
            is_liked = m_is_liked,
            is_processed = False
        )
        session.add(query)
        return True
    