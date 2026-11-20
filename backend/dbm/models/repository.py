from pydantic.v1 import EmailStr
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from .core_models import Dish, Swipe, Ingredient, Tag, UserVector, user_unwanted_ingredients, ReactionType, User
from .schemas import DishesSchema, UserVectorSchema

class DishManager:
    """
    класс отвечающий за перевод инофрмации из БД в ядро.
    с помощью pydantic валидирует и приводит данные в вид, понятный ядру
    """

    async def get_candidate_dishes(self, session: AsyncSession,
                                   user_id: int, limit: int = 200) -> list[dict]:
        """
        берет из таблицы dishes блюда, которые еще не видел пользователь,
        и отправляет их ядру в виде списка словарей
        """
        query = (
                    select(Swipe.dish_id)
                    .where(Swipe.user_id == user_id)
        )
        result = await session.execute(query)
        swipes_id_list = [row[0] for row in result.all()]

        unwanted_query = (
            select(user_unwanted_ingredients.c.ingredient_id)
            .where(user_unwanted_ingredients.c.user_id == user_id)
        )
        unwanted_result = await session.execute(unwanted_query)

        unwanted_ids = [row[0] for row in unwanted_result.all()]

        query = select(Dish).options(selectinload(Dish.tags)).where(Dish.is_public == True)

        if swipes_id_list:
            query = query.where(Dish.id.notin_(swipes_id_list))

        if unwanted_ids:
            query = query.where(~Dish.ingredients.any(Ingredient.id.in_(unwanted_ids)))

        query = query.limit(limit)

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


    async def save_swipe(self, session: AsyncSession, m_dish_id: int, m_user_id: int,
                          m_reaction: ReactionType):

        """
        Сохраняет свайп конкретного пользователя, со всеми данными, был ли лайкнут,
        и тп.
        """

        query = Swipe(
            user_id = m_user_id,
            dish_id = m_dish_id,
            reaction = m_reaction,
            is_processed = False
        )
        session.add(query)
        await session.commit()
        return True


    async def count_unprocessed_swipes(self, session: AsyncSession, user_id: int): 
        from sqlalchemy import func

        query = (
            select(func.count()).select_from(Swipe)
            .where(Swipe.user_id == user_id,
                   Swipe.is_processed == False)
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
            .where(UserVector.user_id == user_id,
                   UserVector.tag_id.in_(tag_deltas.keys()))
        )
        result = await session.execute(query)

        user_vector = {uv.tag_id: uv for uv in result.scalars().all()}

        for tag_id, delta in tag_deltas.items():
            if tag_id in user_vector:
                user_vector[tag_id].weight += delta
            else:
                new_vector_item = UserVector(
                    user_id = user_id,
                    tag_id = tag_id,
                    weight = 5.0 + delta
                )
                session.add(new_vector_item)

        for swipe in unprocessed_swipes:
            swipe.is_processed = True

        await session.commit()


class UserManager:

    async def get_by_id(self, session: AsyncSession, user_id: int):

        query = (select(User).where(User.id == user_id))
        result = await session.execute(query)

        return result.scalar_one_or_none()


    async def get_by_session_id(self, session: AsyncSession, session_id: str):

        query = (select(User).where(User.session_id == session_id))
        result = await session.execute(query)

        return result.scalar_one_or_none()


    async def get_by_email(self, session: AsyncSession, email: EmailStr) -> User:
        query = (select(User).where(User.email == email))
        result = await session.execute(query)

        return result.scalar_one_or_none()

    async def create_guest(self, session: AsyncSession, session_id: str):
        user = User(session_id = session_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    async def create_registered_user(self, session: AsyncSession, session_id: str,
                                     email: EmailStr, hashed_password: str):

        user = User(
            session_id = session_id,
            email = email,
            hashed_password = hashed_password
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)
