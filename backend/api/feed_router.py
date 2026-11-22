from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from backend.dbm.models.core_models import ReactionType
from backend.dbm.models.repository import DishManager
from backend.core.Feed import FeedService
from backend.core.Swipe import SwipeService
from backend.dbm.models.schemas import SwipeRequest

from backend.dbm.database import get_db_session

db_manager = DishManager()
feed_service = FeedService(db_manager)
swipe_service = SwipeService(db_manager)

router = APIRouter(prefix="/feed", tags=["Лента Рекомендаций"])


#Эндпоинты

@router.get("/")
async def get_personal_feed(
    user_id: int, 
    limit: int = 20, 
    session: AsyncSession = Depends(get_db_session)
): 
    """
    Эндпоинт для выдачи ленты.
    Запрос с телефона: GET /feed/?user_id=1&limit=20
    """
    dishes = await feed_service.get_feed(session=session, user_id=user_id, limit=limit)
    
    return {
        "status": "success",
        "data": dishes
    }


@router.post("/swipe")
async def process_swipe(
    request_data: SwipeRequest, 
    session: AsyncSession = Depends(get_db_session)
):
    """
    Эндпоинт для обработки свайпа (лайк/дизлайк/избранное).
    Запрос с телефона: POST /feed/swipe
    Тело (JSON): {"user_id": 1, "dish_id": 5, "reaction": "like"}
    """
    await swipe_service.handle_new_swipe(
        session=session, 
        user_id=request_data.user_id, 
        dish_id=request_data.dish_id, 
        reaction=request_data.reaction
    )
    
    return {
        "status": "success", 
        "message": "Реакция успешно учтена"
    }