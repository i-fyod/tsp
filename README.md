# FastAPI КР4: Миграции, Обработка Ошибок, Валидация и Тестирование

Реализация контрольной работы №4 включает:
- **Задание 9.1**: Alembic миграции БД (SQLite)
- **Задание 10.1-10.2**: Пользовательские обработчики ошибок (CustomExceptionA, CustomExceptionB)
- **Задание 10.2**: Валидация данных с Pydantic (conint, EmailStr, constr)
- **Задание 11.1-11.2**: Асинхронные тесты с pytest-asyncio и Faker

## Структура проекта

```
tsp/
├── main.py                 # FastAPI приложение с эндпоинтами
├── models.py              # SQLAlchemy модели (Product, UserDB)
├── schemas.py             # Pydantic схемы (User, UserOut)
├── database.py            # Конфигурация БД (SQLite)
├── exceptions.py          # Пользовательские исключения
├── alembic/               # Миграции Alembic
│   ├── versions/          # Файлы миграций
│   └── env.py            # Конфиг Alembic
├── tests/
│   └── test_api.py        # Асинхронные тесты (11 тестов)
├── requirements.txt       # Зависимости
└── app.db                 # SQLite БД (создаётся при запуске)
```

## Установка и запуск

### 1. Установка зависимостей

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Запуск приложения

```bash
source venv/bin/activate
python main.py
```

Приложение запустится на `http://127.0.0.1:8000`

### 3. Работа с миграциями

**Просмотр истории миграций:**
```bash
alembic history
```

**Применение миграций:**
```bash
alembic upgrade head
```

**Откат к предыдущей версии:**
```bash
alembic downgrade -1
```

## API Эндпоинты

### POST /users (Задание 10.2, 11.1)
**Создание пользователя** с валидацией:
- `username`: строка (обязательно)
- `age`: integer > 18 (обязательно)
- `email`: EmailStr валиден (обязательно)
- `password`: string 8-16 символов (обязательно)
- `phone`: optional, default "Unknown"

**Пример запроса:**
```json
{
  "username": "john_doe",
  "age": 25,
  "email": "john@example.com",
  "password": "SecurePass123",
  "phone": "555-0123"
}
```

**Ответ (201):**
```json
{
  "id": 1,
  "username": "john_doe",
  "age": 25,
  "email": "john@example.com",
  "phone": "555-0123"
}
```

**Ошибка валидации (422):**
```json
{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "age"],
      "msg": "Input should be greater than 18"
    }
  ]
}
```

### GET /users/{user_id} (Задание 10.2, 11.1)
**Получение пользователя по ID**

**Успех (200):**
```json
{
  "id": 1,
  "username": "john_doe",
  "age": 25,
  "email": "john@example.com",
  "phone": "555-0123"
}
```

**Не найден (404):**
```json
{
  "error": "User not found"
}
```

### DELETE /users/{user_id} (Задание 10.2, 11.1)
**Удаление пользователя**

**Успех:** 204 No Content

**Ошибка:** 404 Not Found

### GET /check-condition/{condition} (Задание 10.1)
**Демонстрация CustomExceptionA**

- `/check-condition/ok` → 200 {"status": "ok"}
- `/check-condition/invalid` → 400 {"error": "Condition 'invalid' is not valid"}

## Обработчики ошибок

### CustomExceptionA (Код 400)
Выбрасывается при нарушении бизнес-логики (задание 10.1)
```python
raise CustomExceptionA("Condition 'invalid' is not valid")
```

### CustomExceptionB (Код 404)
Выбрасывается когда ресурс не найден (задание 10.1)
```python
raise CustomExceptionB("User not found")
```

## Тестирование

### Запуск всех тестов

```bash
source venv/bin/activate
pytest tests/test_api.py -v
```

### Ключевые сценарии (11 тестов)

| Тест | Сценарий | Статус |
|------|----------|--------|
| `test_create_user_201` | Создание → 201 | ✓ |
| `test_get_existing_user_200` | Получение существующего → 200 | ✓ |
| `test_get_nonexistent_user_404` | Получение несуществующего → 404 | ✓ |
| `test_delete_existing_user_204` | Удаление существующего → 204 | ✓ |
| `test_delete_nonexistent_user_404` | Повторное удаление → 404 | ✓ |
| `test_user_validation_age_gt_18` | Валидация age > 18 | ✓ |
| `test_user_validation_email` | Валидация email | ✓ |
| `test_user_validation_password_length` | Валидация пароля (8-16) | ✓ |
| `test_multiple_users_state_isolation` | Изоляция состояния | ✓ |
| `test_custom_exception_a_handler` | CustomExceptionA → 400 | ✓ |
| `test_custom_exception_b_handler` | CustomExceptionB → 404 | ✓ |

### Особенности тестов (Задание 11.2)

- **Асинхронные**: используется `pytest-asyncio`
- **HTTP клиент**: `httpx.AsyncClient` + `ASGITransport` (без реального сервера)
- **Генерация данных**: `Faker` для реалистичных username, email, phone
- **Изоляция**: In-memory SQLite БД, очищается перед каждым тестом
- **Покрытие**: успешные и ошибочные сценарии для всех 3 эндпоинтов

## Миграции БД (Задание 9.1)

### Первая миграция (создание таблиц)
Создаёт таблицы `products` и `users` с полями:

**products:**
- id (Primary Key)
- title (String)
- price (Float)
- count (Integer)
- description (String)

**users:**
- id (Primary Key)
- username (String, unique)
- age (Integer)
- email (String, unique)
- password (String)
- phone (String, default="Unknown")

### Генерирование миграций
```bash
alembic revision --autogenerate -m "Description"
```

### Применение
```bash
alembic upgrade head
```

## Примеры использования

### Создание пользователя
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "age": 30,
    "email": "alice@example.com",
    "password": "MyPassword123",
    "phone": "555-5555"
  }'
```

### Получение пользователя
```bash
curl http://localhost:8000/users/1
```

### Удаление пользователя
```bash
curl -X DELETE http://localhost:8000/users/1
```

### Проверка обработчика ошибок
```bash
curl http://localhost:8000/check-condition/invalid
# Ответ: {"error": "Condition 'invalid' is not valid"}
```

## Команды для проверки

```bash
# 1. Установка
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# 2. Запуск приложения
python main.py

# 3. В другом терминале - запуск тестов
pytest tests/test_api.py -v

# 4. Проверка миграций
alembic history

# 5. Просмотр БД
sqlite3 app.db ".tables"
```

## Статус заданий

- ✅ **Задание 9.1**: Alembic миграции (Product с id, title, price, count)
- ✅ **Задание 10.1**: CustomExceptionA и CustomExceptionB с обработчиками
- ✅ **Задание 10.2**: User с conint(gt=18), EmailStr, constr(8-16), валидация
- ✅ **Задание 11.1**: Модульные асинхронные тесты
- ✅ **Задание 11.2**: Async тесты с pytest-asyncio, httpx, Faker, изоляция состояния

**Все тесты проходят: 11/11 ✓**
