import pytest
from sqlalchemy import select
from backend.dbm.models.core_models import User, Swipe, UserVector, ReactionType

@pytest.mark.asyncio
async def test_get_feed_returns_dishes_from_db(client, db_session, seed_dishes):
    """
    GET /feed/?user_id={id}:
    1. Запрашивает персональную ленту блюд для пользователя.
    2. Из БД извлекаются только публичные блюда.
    3. Каждое блюдо содержит КБЖУ, теги, ингредиенты и скоринг релевантности.
    """
    user = User(session_id="user_feed_test_100")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.get(f"/feed/?user_id={user.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    dishes = body["data"]

    # В фикстуре seed_dishes создано 3 блюда
    assert len(dishes) == 3
    dish_names = [d["name"] for d in dishes]
    assert "Скрэмбл" in dish_names
    assert "Стейк из говядины" in dish_names
    assert "Запеченный лосось" in dish_names

    # Проверяем структуру данных блюда
    first_dish = dishes[0]
    assert "id" in first_dish
    assert "relevance_score" in first_dish
    assert "tags" in first_dish
    assert "proteins" in first_dish
    assert "calories" in first_dish

@pytest.mark.asyncio
async def test_get_feed_empty_when_no_public_dishes(client, db_session):
    """GET /feed/ возвращает пустой список, если нет публичных блюд"""
    user = User(session_id="user_empty_feed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.get(f"/feed/?user_id={user.id}")
    assert response.status_code == 200
    assert response.json()["data"] == []

@pytest.mark.asyncio
async def test_swipe_saves_to_db_and_excludes_from_feed(client, db_session, seed_dishes):
    """
    POST /feed/swipe:
    1. Пользователь свайпает блюдо (например, like).
    2. Запись о свайпе сохраняется в таблицу swipes БД.
    3. При следующем запросе GET /feed/ это блюдо исключается из ленты.
    """
    user = User(session_id="user_swipe_test_200")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    steak = seed_dishes["dishes"]["steak"]

    # 1. Отправляем свайп
    swipe_payload = {
        "user_id": user.id,
        "dish_id": steak.id,
        "reaction": "like"
    }
    swipe_res = await client.post("/feed/swipe", json=swipe_payload)
    assert swipe_res.status_code == 200
    assert swipe_res.json()["status"] == "success"

    # 2. Проверяем наличие записи в БД
    saved_swipe = (await db_session.execute(
        select(Swipe).where(Swipe.user_id == user.id, Swipe.dish_id == steak.id)
    )).scalar_one_or_none()
    assert saved_swipe is not None
    assert saved_swipe.reaction == ReactionType.LIKE
    assert saved_swipe.is_processed is False

    # 3. Проверяем, что стейк исчез из ленты пользователя
    feed_res = await client.get(f"/feed/?user_id={user.id}")
    feed_dishes = feed_res.json()["data"]
    feed_dish_ids = [d["id"] for d in feed_dishes]
    assert steak.id not in feed_dish_ids
    assert len(feed_dishes) == 2

@pytest.mark.asyncio
async def test_swipe_batch_updates_user_vector_in_db(client, db_session, seed_dishes):
    """
    Проверка пакетной обработки свайпов (BATCH_SIZE = 5):
    Когда накапливается 5 свайпов, система пересчитывает вектор интересов пользователя в БД:
    таблица user_vector наполняется весами для тегов, а свайпы помечаются is_processed=True.
    """
    user = User(session_id="user_vector_test_300")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    scramble = seed_dishes["dishes"]["scramble"]

    # Делаем 5 свайпов
    for i in range(5):
        res = await client.post("/feed/swipe", json={
            "user_id": user.id,
            "dish_id": scramble.id,
            "reaction": "favorite"
        })
        assert res.status_code == 200

    # Проверяем, что свайпы стали is_processed = True
    swipes = (await db_session.execute(
        select(Swipe).where(Swipe.user_id == user.id)
    )).scalars().all()
    assert len(swipes) == 5
    assert all(s.is_processed for s in swipes)

    # Проверяем, что в БД создались записи user_vector
    vectors = (await db_session.execute(
        select(UserVector).where(UserVector.user_id == user.id)
    )).scalars().all()
    assert len(vectors) > 0

    # Скрэмбл имеет теги "Завтрак" и "Высокий белок".
    # При 5 свайпах FAVORITE (+2.0 каждый), вес должен вырасти с базовых 5.0 до 5.0 + 5*2.0 = 15.0
    for vec in vectors:
        assert vec.weight > 5.0

@pytest.mark.asyncio
async def test_swipe_invalid_reaction_validation(client):
    """
    POST /feed/swipe:
    Передача неизвестной реакции (например 'super_love') должна возвращать 422.
    """
    res = await client.post("/feed/swipe", json={
        "user_id": 1,
        "dish_id": 1,
        "reaction": "super_love"
    })
    assert res.status_code == 422
