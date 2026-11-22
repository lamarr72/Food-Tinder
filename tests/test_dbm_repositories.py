import pytest
from datetime import date
from sqlalchemy import select
from backend.dbm.models.core_models import (
    User, Tag, Ingredient, Dish, ReactionType, MealType
)
from backend.dbm.models.repository import UserManager, DishManager
from backend.dbm.models.profile_repository import ProfileManager
from backend.dbm.models.ration_repository import RationManager

@pytest.mark.asyncio
async def test_user_manager_crud(db_session):
    """Тестирование передачи данных в UserManager: гость, регистрация, поиск по полям"""
    um = UserManager()

    # 1. Создание гостя
    guest = await um.create_guest(db_session, session_id="sess_repo_001")
    assert guest.id is not None
    assert guest.session_id == "sess_repo_001"

    # 2. Поиск по session_id и по id
    by_sess = await um.get_by_session_id(db_session, "sess_repo_001")
    assert by_sess.id == guest.id

    by_id = await um.get_by_id(db_session, guest.id)
    assert by_id.session_id == "sess_repo_001"

    # 3. Привязка учетных данных
    updated = await um.attach_credentials(
        session=db_session,
        user=guest,
        email="upgraded@test.com",
        hashed_password="hashed_pwd_value"
    )
    assert updated.email == "upgraded@test.com"

    # 4. Поиск по email
    by_email = await um.get_by_email(db_session, "upgraded@test.com")
    assert by_email.id == guest.id

@pytest.mark.asyncio
async def test_dish_manager_create_and_get_by_id(db_session):
    """Тестирование DishManager.create_dish и get_dish_by_id со связями"""
    dm = DishManager()

    # Создаем тег и ингредиент
    tag = Tag(name="Десерт")
    ingr = Ingredient(name="Сахар")
    db_session.add_all([tag, ingr])
    await db_session.commit()

    dish_id = await dm.create_dish(
        session=db_session,
        author_id=1,
        name="Торт Медовик",
        description="Вкусный торт",
        price=350,
        calories=450,
        proteins=6.0,
        fats=18.0,
        carbs=60.0,
        cooking_time=60,
        difficulty=3,
        equipment="Духовка",
        is_public=True,
        tag_ids=[tag.id],
        ingredients=[{"ingredient_id": ingr.id, "quantity": 100.0, "unit": "г"}],
        image_urls=["/static/medovik.jpg"],
        steps=[{"step_number": 1, "description": "Замесить тесто", "image_url": None}]
    )
    assert dish_id is not None

    dish = await dm.get_dish_by_id(db_session, dish_id)
    assert dish is not None
    assert dish["name"] == "Торт Медовик"
    assert dish["equipment"] == "Духовка"
    assert len(dish["tags"]) == 1
    assert dish["tags"][0]["name"] == "Десерт"
    assert len(dish["ingredients"]) == 1
    assert dish["ingredients"][0]["name"] == "Сахар"
    assert len(dish["images"]) == 1
    assert len(dish["steps"]) == 1

@pytest.mark.asyncio
async def test_dish_manager_get_user_favorites(db_session, seed_dishes):
    """Тестирование DishManager.get_user_favorites"""
    dm = DishManager()

    user = User(session_id="user_favs_test")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    steak = seed_dishes["dishes"]["steak"]
    scramble = seed_dishes["dishes"]["scramble"]

    # Сохраняем реакции: стейк - FAVORITE, скрэмбл - LIKE
    await dm.save_swipe(db_session, steak.id, user.id, ReactionType.FAVORITE)
    await dm.save_swipe(db_session, scramble.id, user.id, ReactionType.LIKE)

    favorites = await dm.get_user_favorites(db_session, user.id)
    assert len(favorites) == 1
    assert favorites[0]["name"] == "Стейк из говядины"

@pytest.mark.asyncio
async def test_dish_manager_unwanted_ingredients_filtering(db_session, seed_dishes):
    """
    Проверка фильтрации DishManager:
    Если у пользователя в БД есть ингредиент в черном списке,
    блюдо с этим ингредиентом исключается из выборки get_candidate_dishes.
    """
    dm = DishManager()
    pm = ProfileManager()

    user = User(session_id="user_allergy_test")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Добавляем лосось в аллергены пользователя
    salmon_ingr = seed_dishes["ingredients"]["salmon"]
    await pm.set_unwanted_ingredients(db_session, user.id, [salmon_ingr.id])

    # Получаем блюда-кандидаты
    candidates = await dm.get_candidate_dishes(db_session, user_id=user.id)
    names = [c["name"] for c in candidates]

    # Лосось должен быть отфильтрован, а стейк и скрэмбл должны остаться
    assert "Запеченный лосось" not in names
    assert "Скрэмбл" in names
    assert "Стейк из говядины" in names

@pytest.mark.asyncio
async def test_profile_manager_lifecycle(db_session):
    """Тестирование ProfileManager: чтение, редактирование профиля, справочники тегов и ингредиентов"""
    pm = ProfileManager()

    user = User(
        email="profile_user@test.com",
        session_id="profile_sess_100",
        name="Алексей",
        height=180,
        weight=75.5,
        gender="male",
        birth_date=date(1995, 5, 20)
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 1. Получение профиля
    profile = await pm.get_profile(db_session, user.id)
    assert profile["name"] == "Алексей"
    assert profile["height"] == 180
    assert profile["weight"] == 75.5
    assert profile["birth_date"] == "1995-05-20"

    # 2. Обновление профиля
    success = await pm.update_profile(
        db_session,
        user_id=user.id,
        name="Алексей Смирнов",
        weight=78.0
    )
    assert success is True

    updated_profile = await pm.get_profile(db_session, user.id)
    assert updated_profile["name"] == "Алексей Смирнов"
    assert updated_profile["weight"] == 78.0
    assert updated_profile["height"] == 180  # Рост не изменился

    # 3. Справочники
    tags = await pm.get_all_tags(db_session)
    ingrs = await pm.get_all_ingredients(db_session)
    assert isinstance(tags, list)
    assert isinstance(ingrs, list)

@pytest.mark.asyncio
async def test_ration_manager_crud(db_session, seed_dishes):
    """Тестирование RationManager: добавление, получение, обновление, удаление и очистка рациона"""
    rm = RationManager()

    user = User(session_id="ration_user_test")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    steak = seed_dishes["dishes"]["steak"]

    # 1. Добавление в рацион
    item_id = await rm.add_ration_item(
        session=db_session,
        user_id=user.id,
        dish_id=steak.id,
        meal_type=MealType.DINNER,
        day_number=1,
        portion_grams=250
    )
    assert item_id is not None

    # 2. Получение рациона
    items = await rm.get_ration_items(db_session, user.id)
    assert len(items) == 1
    item = items[0]
    assert item["day_number"] == 1
    assert item["portion_grams"] == 250
    assert item["dish"]["name"] == "Стейк из говядины"

    # 3. Обновление позиции
    await rm.update_ration_item(db_session, item_id=item_id, user_id=user.id, portion_grams=300)
    items_after = await rm.get_ration_items(db_session, user.id)
    assert items_after[0]["portion_grams"] == 300

    # 4. Удаление
    deleted = await rm.delete_ration_item(db_session, item_id=item_id, user_id=user.id)
    assert deleted is True
    items_empty = await rm.get_ration_items(db_session, user.id)
    assert len(items_empty) == 0
