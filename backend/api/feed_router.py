from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from dbm.models.core_models import ReactionType
from dbm.models.repository import DishManager
from core.Feed import FeedService
from core.Swipe import SwipeService

from dbm.database import get_db_session

db_manager = DishManager()
feed_service = FeedService(db_manager)
swipe_service = SwipeService(db_manager)

router = APIRouter(prefix="/feed", tags=["Лента Рекомендаций"])



class SwipeRequest(BaseModel):
    """
    Схема для POST-запроса. 
    Если фронтенд пришлет reaction="super_like", FastAPI автоматически 
    выдаст ошибку 422, так как такого значения нет в ReactionType.
    """
    user_id: int
    dish_id: int
    reaction: ReactionType


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