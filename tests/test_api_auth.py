import pytest
from sqlalchemy import select
from backend.dbm.models.core_models import User
from backend.core.auth import AuthService

@pytest.mark.asyncio
async def test_root_healthcheck(client):
    """Проверка доступности корневого эндпоинта API"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Food Tinder" in data["message"]

@pytest.mark.asyncio
async def test_guest_login_creates_new_user_in_db(client, db_session):
    """
    POST /auth/guest:
    1. Передает session_id из фронтенда в API.
    2. API создает новую запись User в БД с этим session_id.
    3. Возвращает валидный JWT токен со статусом гостя.
    """
    session_id = "device_guest_unique_12345"
    response = await client.post("/auth/guest", json={"session_id": session_id})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Проверяем, что в БД реально появилась запись
    user = (await db_session.execute(select(User).where(User.session_id == session_id))).scalar_one_or_none()
    assert user is not None
    assert user.session_id == session_id
    assert user.email is None

    # Декодируем токен и проверяем payload
    token_payload = AuthService.decode_access_token(data["access_token"])
    assert token_payload["sub"] == str(user.id)
    assert token_payload["is_guest"] is True

@pytest.mark.asyncio
async def test_guest_login_existing_user_no_duplicate(client, db_session):
    """
    POST /auth/guest:
    Повторный вход с тем же session_id не должен создавать дубликат в БД,
    а должен возвращать токен для уже существующего пользователя.
    """
    session_id = "device_guest_repeat_54321"
    res1 = await client.post("/auth/guest", json={"session_id": session_id})
    res2 = await client.post("/auth/guest", json={"session_id": session_id})

    assert res1.status_code == 200
    assert res2.status_code == 200

    users = (await db_session.execute(select(User).where(User.session_id == session_id))).scalars().all()
    assert len(users) == 1

@pytest.mark.asyncio
async def test_register_user_updates_guest_to_registered(client, db_session):
    """
    POST /auth/register:
    Превращает гостевой профиль в зарегистрированного пользователя:
    записывает email и захэшированный пароль в существующую запись БД.
    """
    session_id = "guest_to_upgrade_99999"
    # 1. Вход гостя
    await client.post("/auth/guest", json={"session_id": session_id})

    # 2. Регистрация гостя
    email = "newuser@example.com"
    password = "secret_password_123"
    reg_response = await client.post("/auth/register", json={
        "session_id": session_id,
        "email": email,
        "password": password
    })

    assert reg_response.status_code == 200
    reg_data = reg_response.json()
    assert "access_token" in reg_data

    # Проверяем запись в БД
    user = (await db_session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    assert user is not None
    assert user.session_id == session_id
    assert user.email == email
    assert user.hashed_password is not None
    assert user.hashed_password != password  # Пароль захеширован, а не в открытом виде

    # Проверяем токен
    payload = AuthService.decode_access_token(reg_data["access_token"])
    assert payload["sub"] == str(user.id)
    assert payload["is_guest"] is False

@pytest.mark.asyncio
async def test_register_duplicate_email_conflict(client):
    """
    POST /auth/register:
    Попытка зарегистрировать уже занятый email должна возвращать ошибку 409 Conflict.
    """
    session1 = "guest_session_11111"
    session2 = "guest_session_22222"
    email = "duplicate@example.com"
    password = "valid_password_123"

    res1 = await client.post("/auth/register", json={
        "session_id": session1,
        "email": email,
        "password": password
    })
    assert res1.status_code == 200

    res2 = await client.post("/auth/register", json={
        "session_id": session2,
        "email": email,
        "password": password
    })
    assert res2.status_code == 409
    assert "уже существует" in res2.json()["detail"]

@pytest.mark.asyncio
async def test_login_user_success_and_failures(client):
    """
    POST /auth/login:
    1. Успешный логин зарегистрированного пользователя по email и паролю.
    2. Отклонение при неверном пароле (401).
    3. Отклонение при несуществующем email (401).
    """
    session_id = "guest_for_login_33333"
    email = "login_test@example.com"
    password = "correct_password_123"

    # Регистрируем
    await client.post("/auth/register", json={
        "session_id": session_id,
        "email": email,
        "password": password
    })

    # 1. Успешный вход
    login_res = await client.post("/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data

    # 2. Неверный пароль
    bad_pass_res = await client.post("/auth/login", json={
        "email": email,
        "password": "wrong_password_999"
    })
    assert bad_pass_res.status_code == 401

    # 3. Несуществующий пользователь
    not_found_res = await client.post("/auth/login", json={
        "email": "ghost@example.com",
        "password": password
    })
    assert not_found_res.status_code == 401

@pytest.mark.asyncio
async def test_auth_validation_errors(client):
    """
    Проверка Pydantic валидации:
    Короткий session_id, некорректный email, слишком короткий пароль -> 422 Unprocessable Entity.
    """
    # Слишком короткий session_id (min_length=10)
    res = await client.post("/auth/guest", json={"session_id": "short"})
    assert res.status_code == 422

    # Невалидный email
    res2 = await client.post("/auth/register", json={
        "session_id": "valid_session_123",
        "email": "not-an-email",
        "password": "valid_password_123"
    })
    assert res2.status_code == 422
