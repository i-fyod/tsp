import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from faker import Faker
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db
from models import UserDB

# Настройка in-memory БД для тестов
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

fake = Faker()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clear_db():
    """Очистка БД перед каждым тестом"""
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest_asyncio.fixture
async def async_client():
    """Асинхронный HTTP клиент для тестов"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_user_201(async_client):
    """Задание 11.2: Создание пользователя возвращает 201"""
    user_data = {
        "username": fake.user_name(),
        "age": fake.random_int(min=19, max=60),
        "email": fake.email(),
        "password": fake.password(length=10, special_chars=False),
        "phone": fake.phone_number()
    }
    response = await async_client.post("/users", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["age"] == user_data["age"]
    assert data["email"] == user_data["email"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_existing_user_200(async_client):
    """Задание 11.2: Получение существующего пользователя возвращает 200"""
    # Создаём пользователя
    user_data = {
        "username": fake.user_name(),
        "age": fake.random_int(min=19, max=60),
        "email": fake.email(),
        "password": fake.password(length=10),
        "phone": "555-0123"
    }
    response = await async_client.post("/users", json=user_data)
    user_id = response.json()["id"]

    # Получаем пользователя
    response = await async_client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == user_data["username"]


@pytest.mark.asyncio
async def test_get_nonexistent_user_404(async_client):
    """Задание 11.2: Попытка получить несуществующего пользователя возвращает 404"""
    response = await async_client.get("/users/999")
    assert response.status_code == 404
    assert "error" in response.json()


@pytest.mark.asyncio
async def test_delete_existing_user_204(async_client):
    """Задание 11.2: Удаление существующего пользователя возвращает 204"""
    # Создаём пользователя
    user_data = {
        "username": fake.user_name(),
        "age": fake.random_int(min=19, max=60),
        "email": fake.email(),
        "password": fake.password(length=12),
        "phone": "555-0124"
    }
    response = await async_client.post("/users", json=user_data)
    user_id = response.json()["id"]

    # Удаляем пользователя
    response = await async_client.delete(f"/users/{user_id}")
    assert response.status_code == 204

    # Проверяем что пользователь удалён
    response = await async_client.get(f"/users/{user_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_user_404(async_client):
    """Задание 11.2: Повторное удаление того же пользователя возвращает 404"""
    response = await async_client.delete("/users/999")
    assert response.status_code == 404
    assert "error" in response.json()


@pytest.mark.asyncio
async def test_user_validation_age_gt_18(async_client):
    """Задание 10.2, 11.1: Валидация age > 18"""
    user_data = {
        "username": fake.user_name(),
        "age": 18,  # Не валидно, нужно > 18
        "email": fake.email(),
        "password": fake.password(length=10),
    }
    response = await async_client.post("/users", json=user_data)
    assert response.status_code == 422  # Validation error
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_user_validation_email(async_client):
    """Задание 10.2, 11.1: Валидация email"""
    user_data = {
        "username": fake.user_name(),
        "age": fake.random_int(min=19, max=60),
        "email": "invalid-email",  # Не валиден
        "password": fake.password(length=10),
    }
    response = await async_client.post("/users", json=user_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_user_validation_password_length(async_client):
    """Задание 10.2, 11.1: Валидация пароля (8-16 символов)"""
    # Короткий пароль
    user_data = {
        "username": fake.user_name(),
        "age": fake.random_int(min=19, max=60),
        "email": fake.email(),
        "password": "short",  # < 8
    }
    response = await async_client.post("/users", json=user_data)
    assert response.status_code == 422

    # Длинный пароль
    user_data = {
        "username": fake.user_name(),
        "age": fake.random_int(min=19, max=60),
        "email": fake.email(),
        "password": "a" * 17,  # > 16
    }
    response = await async_client.post("/users", json=user_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_multiple_users_state_isolation(async_client):
    """Задание 11.2: Состояние изолировано между тестами"""
    # Создаём двух пользователей
    user1 = {
        "username": fake.user_name(),
        "age": fake.random_int(min=19, max=60),
        "email": fake.email(),
        "password": fake.password(length=10),
    }
    response1 = await async_client.post("/users", json=user1)
    assert response1.status_code == 201

    user2 = {
        "username": fake.user_name(),
        "age": fake.random_int(min=19, max=60),
        "email": fake.email(),
        "password": fake.password(length=10),
    }
    response2 = await async_client.post("/users", json=user2)
    assert response2.status_code == 201

    # Проверяем что оба существуют
    id1 = response1.json()["id"]
    id2 = response2.json()["id"]
    
    response = await async_client.get(f"/users/{id1}")
    assert response.status_code == 200
    
    response = await async_client.get(f"/users/{id2}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_custom_exception_a_handler(async_client):
    """Задание 10.1: CustomExceptionA возвращает 400"""
    response = await async_client.get("/check-condition/invalid")
    assert response.status_code == 400
    assert "error" in response.json()


@pytest.mark.asyncio
async def test_custom_exception_b_handler(async_client):
    """Задание 10.1: CustomExceptionB возвращает 404"""
    response = await async_client.get("/users/9999")
    assert response.status_code == 404
    assert "error" in response.json()
