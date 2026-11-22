import pytest
from backend.core.auth import AuthService
from backend.core.Feed import FeedService
from backend.core.Ration import RationService
from backend.dbm.models.core_models import MealType, ReactionType
from backend.dbm.models.repository import DishManager, UserManager
from backend.dbm.models.ration_repository import RationManager

def test_auth_service_password_hashing_and_jwt():
    """Тестирование хэширования паролей bcrypt и создания/декодирования JWT токенов"""
    user_manager = UserManager()
    auth_service = AuthService(user_manager)

    password = "SuperSecurePassword123!"
    hashed = auth_service.hash_password(password)

    assert isinstance(hashed, str)
    assert hashed != password
    assert auth_service.check_password(password, hashed) is True
    assert auth_service.check_password("WrongPassword", hashed) is False

    # Генерация и валидация JWT
    token = auth_service.create_access_token(user_id=42, is_guest=False)
    payload = auth_service.decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["is_guest"] is False
    assert "exp" in payload

@pytest.mark.asyncio
async def test_feed_service_scoring_algorithm(db_session, seed_dishes):
    """
    Тестирование алгоритма скоринга FeedService:
    Блюда с тегами, имеющими больший вес в векторе пользователя,
    должны подниматься наверх ленты.
    """
    from backend.dbm.models.core_models import User, UserVector

    dm = DishManager()
    feed_service = FeedService(dm)

    user = User(session_id="feed_algo_user")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Добавляем пользователю повышенный интерес к "Рыба" (вес 15.0) и нейтральный к "Мясо" (5.0)
    fish_tag = seed_dishes["tags"]["fish"]
    meat_tag = seed_dishes["tags"]["meat"]

    db_session.add(UserVector(user_id=user.id, tag_id=fish_tag.id, weight=15.0))
    db_session.add(UserVector(user_id=user.id, tag_id=meat_tag.id, weight=2.0))
    await db_session.commit()

    # Запрашиваем ленту
    feed = await feed_service.get_feed(db_session, user.id)

    # Первым блюдом должен быть лосось (рыба с наибольшим весом)
    assert len(feed) > 0
    assert feed[0]["name"] == "Запеченный лосось"
    assert feed[0]["relevance_score"] > feed[-1]["relevance_score"]

@pytest.mark.asyncio
async def test_ration_service_stats_calculation(db_session, seed_dishes):
    """
    Тестирование калькуляции КБЖУ и цен в RationService:
    Проверяет пересчет с учетом веса порции: portion_grams / 100.
    """
    from backend.dbm.models.core_models import User

    rm = RationManager()
    ration_service = RationService(rm)

    user = User(session_id="ration_calc_user")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    steak = seed_dishes["dishes"]["steak"]  # price: 600, calories: 550, proteins: 45.0, fats: 35.0, carbs: 0.0

    # Добавляем порцию 200 грамм (фактор = 2.0)
    await rm.add_ration_item(
        session=db_session,
        user_id=user.id,
        dish_id=steak.id,
        meal_type=MealType.LUNCH,
        day_number=1,
        portion_grams=200
    )

    full_ration = await ration_service.get_full_ration(db_session, user.id)
    assert len(full_ration["days"]) == 1

    day1 = full_ration["days"][0]
    stats = day1["stats"]

    # При 200г: калории = 550 * 2 = 1100, цена = 600 * 2 = 1200
    assert stats["calories"] == 1100.0
    assert stats["price"] == 1200.0
    assert stats["proteins"] == 90.0
    assert stats["fats"] == 70.0

    # Общий итог
    assert full_ration["total"]["calories"] == 1100.0
    assert full_ration["total"]["price"] == 1200.0

@pytest.mark.asyncio
async def test_ration_service_auto_generation(db_session, seed_dishes):
    """Тестирование автоматической генерации рациона на N дней из избранных блюд"""
    from backend.dbm.models.core_models import User

    dm = DishManager()
    rm = RationManager()
    ration_service = RationService(rm)

    user = User(session_id="ration_autogen_user")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    scramble = seed_dishes["dishes"]["scramble"]
    steak = seed_dishes["dishes"]["steak"]

    # Добавляем блюда в избранное/лайки
    await dm.save_swipe(db_session, scramble.id, user.id, ReactionType.FAVORITE)
    await dm.save_swipe(db_session, steak.id, user.id, ReactionType.LIKE)

    # Генерируем рацион на 2 дня
    ration = await ration_service.auto_generate_ration(
        session=db_session,
        user_id=user.id,
        days_count=2,
        meals=[MealType.BREAKFAST, MealType.LUNCH]
    )

    assert len(ration["days"]) == 2
    for day in ration["days"]:
        assert len(day["items"]) == 2
        assert day["stats"]["calories"] > 0
