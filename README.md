# FastAPI Учебное приложение - Контрольная работа №3

Институт: ИПТИП  
Дисциплина: Технологии разработки серверных приложений  
Преподаватель: Дворецкий Артур Геннадьевич  

## Обзор

Данное приложение реализует все требуемые задачи из контрольной работы №3 по FastAPI:

- **Задание 6.1**: Базовая HTTP-аутентификация `/login` (GET)
- **Задание 6.2**: Хеширование паролей с Bcrypt + `/register` + `/login`
- **Задание 6.3**: Защита документации (режимы DEV/PROD)
- **Задание 6.4**: JWT-аутентификация
- **Задание 6.5**: Расширенная JWT + Ограничение частоты запросов (Rate Limiting)
- **Задание 7.1**: Управление доступом на основе ролей (RBAC)
- **Задание 8.1**: Регистрация пользователей в SQLite
- **Задание 8.2**: CRUD-операции с ресурсом Todo

## Установка

```bash
# Создание виртуального окружения (рекомендуется)
python -m venv venv

# Активация виртуального окружения
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

## Запуск приложения

```bash
# Запуск сервера
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Альтернативный запуск через Python
python main.py
```

После запуска сервер будет доступен по адресу: http://localhost:8000

## Переменные окружения

Скопируйте `.env.example` в `.env` и настройте:

```bash
MODE=DEV           # DEV или PROD
DOCS_USER=admin    # Имя пользователя для доступа к документации (режим DEV)
DOCS_PASSWORD=admin123  # Пароль для доступа к документации (режим DEV)
SECRET_KEY=your-secret-key  # Секретный ключ для JWT
```

## Эндпоинты API

### Аутентификация (Задания 6.1, 6.2)

```bash
# Регистрация нового пользователя
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"correctpass"}' \
  http://localhost:8000/register

# Вход с базовой аутентификацией (GET)
curl -u user1:correctpass http://localhost:8000/login
```

### JWT-аутентификация (Задания 6.4, 6.5)

```bash
# Вход с получением JWT-токена (POST)
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"correctpass"}' \
  http://localhost:8000/login

# Доступ к защищенному ресурсу
curl -H "Authorization: Bearer <токен>" \
  http://localhost:8000/protected_resource
```

### RBAC (Задание 7.1)

```bash
# Ресурс администратора
curl -H "Authorization: Bearer <токен>" \
  http://localhost:8000/admin_resource

# Ресурс пользователя
curl -H "Authorization: Bearer <токен>" \
  http://localhost:8000/user_resource

# Ресурс гостя
curl -H "Authorization: Bearer <токен>" \
  http://localhost:8000/guest_resource

# Получить все роли
curl http://localhost:8000/roles
```

### База данных (Задание 8.1)

```bash
# Регистрация пользователя в SQLite
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"test_user","password":"12345"}' \
  http://localhost:8000/db/register
```

### Todo CRUD (Задание 8.2)

```bash
# Создать Todo
curl -X POST -H "Content-Type: application/json" \
  -d '{"title":"Купить продукты","description":"Молоко, яйца, хлеб"}' \
  http://localhost:8000/todos

# Получить Todo по ID
curl http://localhost:8000/todos/1

# Обновить Todo
curl -X PUT -H "Content-Type: application/json" \
  -d '{"title":"Купить продукты","description":"Молоко, яйца, хлеб, масло","completed":true}' \
  http://localhost:8000/todos/1

# Удалить Todo
curl -X DELETE http://localhost:8000/todos/1

# Получить все Todo
curl http://localhost:8000/todos
```

## Тестирование

Приложение можно тестировать с помощью curl-команд, указанных выше. Все эндпоинты возвращают соответствующие HTTP-коды состояния:

- `200 OK` - Успешный запрос
- `201 Created` - Ресурс создан
- `401 Unauthorized` - Ошибка аутентификации
- `403 Forbidden` - Недостаточно прав
- `404 Not Found` - Ресурс не найден
- `409 Conflict` - Пользователь уже существует
- `429 Too Many Requests` - Превышен лимит запросов

## Структура проекта

```
.
├── app/
│   ├── __init__.py
│   └── config.py          # Конфигурация настроек
├── main.py                # Основное приложение
├── requirements.txt       # Python-зависимости
├── .env                   # Переменные окружения
├── .env.example          # Шаблон переменных окружения
└── README.md              # Этот файл
```

## Режимы работы

### Режим DEV
- Документация доступна по адресу `/docs`
- Требуется базовая аутентификация для доступа к документации
- Используйте `MODE=DEV` в `.env`

### Режим PROD
- Документация полностью скрыта (`/docs`, `/redoc`, `/openapi.json` возвращают 404)
- Используйте `MODE=PROD` в `.env`

## Примечания

- Пароли хешируются с использованием Bcrypt
- JWT-токены истекают через 30 минут (по умолчанию)
- Ограничение частоты запросов: `/register` - 1/мин, `/login` - 5/мин
- Для сравнения строк используется `secrets.compare_digest()` для защиты от тайминг-атак
- Пользователи хранятся в памяти (для заданий 6.x-7.x) и в SQLite (для задания 8.1)
