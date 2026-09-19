from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession 

class DishManager:

    async def get_candidate_dishes(self, session: AsyncSession,
                                    user_id: int, limit: int = 20) -> list[dict]:

        return      

    async def get_user_vector():
        
        return

    async def save_swipe():
        return
    