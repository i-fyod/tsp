# FastAPI КР2 - Контрольная работа №2

Полная реализация всех 7 заданий контрольной работы по FastAPI.

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
python kr2_app.py
```

или

```bash
uvicorn kr2_app:app --reload --host 0.0.0.0 --port 8000
```

Приложение будет доступно по адресу `http://localhost:8000`

Документация (Swagger UI): `http://localhost:8000/docs`

---

## Задания и примеры запросов

### Task 3.1: User Creation

**POST /create_user**

Создание пользователя с валидацией данных.

**Пример запроса:**
```bash
curl -X POST "http://localhost:8000/create_user" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice",
    "email": "alice@example.com",
    "age": 30,
    "is_subscribed": true
  }'
```

**Ожидаемый ответ:**
```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "age": 30,
  "is_subscribed": true
}
```

**Валидация:**
- `name` - обязательно
- `email` - обязательно, валидный формат
- `age` - опционально, должно быть положительным числом
- `is_subscribed` - опционально (по умолчанию false)

---

### Task 3.2: Product Search and Retrieval

**GET /product/{product_id}**

Получение информации о продукте по ID.

**Пример запроса:**
```bash
curl "http://localhost:8000/product/123"
```

**Ожидаемый ответ:**
```json
{
  "product_id": 123,
  "name": "Smartphone",
  "category": "Electronics",
  "price": 599.99
}
```

---

**GET /products/search**

Поиск товаров по ключевому слову с опциональной фильтрацией.

**Параметры:**
- `keyword` (обязательно) - ключевое слово для поиска
- `category` (опционально) - категория для фильтрации
- `limit` (опционально, по умолчанию 10) - максимум результатов

**Пример запроса:**
```bash
curl "http://localhost:8000/products/search?keyword=phone&category=Electronics&limit=5"
```

**Ожидаемый ответ:**
```json
[
  {
    "product_id": 123,
    "name": "Smartphone",
    "category": "Electronics",
    "price": 599.99
  },
  {
    "product_id": 789,
    "name": "Iphone",
    "category": "Electronics",
    "price": 1299.99
  }
]
```

---

### Task 5.1: Basic Cookie Authentication

**POST /login**

Логин пользователя с установкой cookie `session_token`.

**Параметры (form-data или query):**
- `username` - имя пользователя (demo: "user123")
- `password` - пароль (demo: "password123")

**Пример запроса:**
```bash
curl -X POST "http://localhost:8000/login" \
  -d "username=user123&password=password123" \
  -v
```

**GET /user**

Получение профиля пользователя (требует валидной cookie `session_token`).

**Пример запроса:**
```bash
curl "http://localhost:8000/user" \
  -H "Cookie: session_token=<YOUR_SESSION_TOKEN>"
```

**Ошибка без cookie:**
```json
{
  "detail": "Unauthorized"
}
```

---

### Task 5.2: Signed Cookie Authentication

**POST /login_signed**

Логин с подписанным токеном (itsdangerous).

**Пример запроса:**
```bash
curl -X POST "http://localhost:8000/login_signed" \
  -d "username=user123&password=password123" \
  -v
```

**GET /profile**

Получение профиля с проверкой подписи.

**Пример запроса:**
```bash
curl "http://localhost:8000/profile" \
  -H "Cookie: session_token=<YOUR_SIGNED_TOKEN>"
```

---

### Task 5.3: Dynamic Session with 3-5 Minute Refresh

**POST /login_dynamic**

Логин с динамической сессией (логика 3-5 минут).

**Пример запроса:**
```bash
curl -X POST "http://localhost:8000/login_dynamic" \
  -d "username=user123&password=password123" \
  -v
```

**GET /profile_dynamic**

Получение профиля с автоматическим продлением сессии.

**Логика:**
- Сессия действует 5 минут
- Если запрос в первые 3 минуты → cookie не обновляется
- Если запрос между 3 и 5 минутами → cookie обновляется на новые 5 минут
- Если запрос после 5 минут → статус 401 "Session expired"

**Пример запроса:**
```bash
curl "http://localhost:8000/profile_dynamic" \
  -H "Cookie: session_token=<YOUR_DYNAMIC_TOKEN>"
```

---

### Task 5.4: Headers Extraction

**GET /headers**

Извлечение и возврат заголовков `User-Agent` и `Accept-Language`.

**Обязательные заголовки:**
- `User-Agent`
- `Accept-Language` (должен иметь валидный формат, например "en-US,en;q=0.9")

**Пример запроса:**
```bash
curl "http://localhost:8000/headers" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
  -H "Accept-Language: en-US,en;q=0.9,es;q=0.8"
```

**Ожидаемый ответ:**
```json
{
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  "Accept-Language": "en-US,en;q=0.9,es;q=0.8"
}
```

**Ошибка без заголовков:**
```json
{
  "detail": "User-Agent header is required"
}
```

---

### Task 5.5: CommonHeaders Model

**GET /info**

Получение информации с переиспользуемой моделью `CommonHeaders`.

Возвращает заголовки и добавляет HTTP-заголовок `X-Server-Time`.

**Пример запроса:**
```bash
curl "http://localhost:8000/info" \
  -H "User-Agent: Mozilla/5.0" \
  -H "Accept-Language: en-US,en;q=0.9" \
  -v
```

**Ожидаемый ответ:**
```json
{
  "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
  "headers": {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
  }
}
```

**Заголовки ответа:**
```
X-Server-Time: 2026-04-01T15:30:45.123456
```

---

**GET /headers_v2**

Альтернативный маршрут с моделью `CommonHeaders`.

**Пример запроса:**
```bash
curl "http://localhost:8000/headers_v2" \
  -H "User-Agent: Mozilla/5.0" \
  -H "Accept-Language: en-US,en;q=0.9"
```

**Ожидаемый ответ:**
```json
{
  "User-Agent": "Mozilla/5.0",
  "Accept-Language": "en-US,en;q=0.9"
}
```

---

## Тестирование с Postman

1. Импортируйте коллекцию или создайте запросы вручную
2. Для задач 5.1-5.3 используйте функцию "Manage Cookies" в Postman
3. Для заголовков явно указывайте `User-Agent` и `Accept-Language`

## Структура кода

```
kr2_app.py
├── Task 3.1: UserCreate model & /create_user endpoint
├── Task 3.2: Product data & search/retrieval functions
├── Task 5.1: Basic cookie auth (sessions_basic)
├── Task 5.2: Signed cookie auth (itsdangerous)
├── Task 5.3: Dynamic session with 3-5 min refresh logic
├── Task 5.4: Header extraction (/headers)
└── Task 5.5: CommonHeaders model & /info, /headers_v2
```

## Демо учетные данные

- **username:** user123
- **password:** password123

---

Все задания реализованы согласно ТЗ без добавления функционала поверх требуемого.
