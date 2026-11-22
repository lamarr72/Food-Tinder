# все для работы с профилем пользователя, спиком аллергенов и справочниками тегов/индегридиентов для фильтров. 
from datetime import date
from sqlalchemy import select, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from .core_models import User, Ingredient, Tag, user_unwanted_ingredients


class ProfileManager:
    """
    работа с профилем пользователя, аллергенами и справочниками в БД
    """

    async def get_profile(self, session: AsyncSession, user_id: int) -> dict | None:
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None

        unwanted = await self.get_unwanted_ingredients(session, user_id)

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "birth_date": user.birth_date.isoformat() if user.birth_date else None,
            "height": user.height,
            "weight": user.weight,
            "gender": user.gender,
            "avatar_url": user.avatar_url,
            "unwanted_ingredients": unwanted
        }

    async def update_profile(
        self,
        session: AsyncSession,
        user_id: int,
        name: str | None = None,
        birth_date: date | None = None,
        height: int | None = None,
        weight: float | None = None,
        gender: str | None = None,
        avatar_url: str | None = None
    ) -> bool:
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return False

        if name is not None:
            user.name = name
        if birth_date is not None:
            user.birth_date = birth_date
        if height is not None:
            user.height = height
        if weight is not None:
            user.weight = weight
        if gender is not None:
            user.gender = gender
        if avatar_url is not None:
            user.avatar_url = avatar_url

        await session.commit()
        return True

    async def get_unwanted_ingredients(self, session: AsyncSession, user_id: int) -> list[dict]:
        query = (
            select(Ingredient.id, Ingredient.name)
            .join(
                user_unwanted_ingredients,
                Ingredient.id == user_unwanted_ingredients.c.ingredient_id
            )
            .where(user_unwanted_ingredients.c.user_id == user_id)
            .order_by(Ingredient.name)
        )
        result = await session.execute(query)
        return [{"id": row.id, "name": row.name} for row in result.all()]

    async def set_unwanted_ingredients(
        self,
        session: AsyncSession,
        user_id: int,
        ingredient_ids: list[int]
    ) -> bool:
        """
        перезаписывает список аллергенов пользователя
        """
        await session.execute(
            delete(user_unwanted_ingredients).where(
                user_unwanted_ingredients.c.user_id == user_id
            )
        )

        unique_ids = list(set(ingredient_ids))
        if unique_ids:
            rows = [{"user_id": user_id, "ingredient_id": ing_id} for ing_id in unique_ids]
            await session.execute(insert(user_unwanted_ingredients), rows)

        await session.commit()
        return True

    async def get_all_ingredients(self, session: AsyncSession) -> list[dict]:
        query = select(Ingredient.id, Ingredient.name).order_by(Ingredient.name)
        result = await session.execute(query)
        return [{"id": row.id, "name": row.name} for row in result.all()]

    async def get_all_tags(self, session: AsyncSession) -> list[dict]:
        query = select(Tag.id, Tag.name).order_by(Tag.name)
        result = await session.execute(query)
        return [{"id": row.id, "name": row.name} for row in result.all()]