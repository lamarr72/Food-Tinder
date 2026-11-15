#Логика обработки лайк/дизлайк

from sqlalchemy.ext.asyncio import AsyncSession
from dbm.models.core_models import ReactionType

BATCH_SIZE = 5
class SwipeService:
    """
    Логика обработки реакций пользователя.
    Управляет сохранением свайпов и решает, когда 
    нужно обьновлять вектор пользователя
    """

    def __init__(self, db_manager):
        self.db = db_manager

    async def handle_new_swipe(self, session: AsyncSession, user_id: int, 
                               dish_id: int, reaction: ReactionType) -> bool:

        """
        Главный метод обработки одного свайпа
        """

        await self.db.save_swipe(
            session=session, 
            m_dish_id=dish_id, 
            m_user_id=user_id, 
            m_reaction=reaction
        )

        unrpocessed_count = await self.db.count_unprocessed_swipes(session, user_id)

        if unrpocessed_count >= BATCH_SIZE:
            await self.db.process_vector_batch(session, user_id)

        return True
