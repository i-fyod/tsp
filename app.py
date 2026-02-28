from fastapi import FastAPI
from fastapi.responses import FileResponse

from models import CalculateRequest, Feedback, User, UserWithAge

app = FastAPI()

# Хранилище отзывов (задание 2.1 + 2.2)
feedbacks: list[dict] = []

# Экземпляр User для задания 1.4
user_instance = User(name="Иван Иванов", id=1)


# --- Задание 1.1 ---
# GET / → JSON-сообщение
@app.get("/")
def root():
    return {"message": "Авторелоад действительно работает"}


# --- Задание 1.2 ---
# GET /index → HTML-страница
@app.get("/index")
def index_page():
    return FileResponse("index.html")


# --- Задание 1.3 ---
# POST /calculate → сумма двух чисел
@app.post("/calculate")
def calculate(data: CalculateRequest):
    return {"result": data.num1 + data.num2}


# --- Задание 1.4 ---
# GET /users → данные пользователя
@app.get("/users")
def get_users():
    return user_instance.model_dump()


# --- Задание 1.5 ---
# POST /user → проверка is_adult
@app.post("/user")
def check_user(data: UserWithAge):
    is_adult = data.age >= 18
    return {"name": data.name, "age": data.age, "is_adult": is_adult}


# --- Задание 2.1 + 2.2 ---
# POST /feedback → отзыв с валидацией
@app.post("/feedback")
def create_feedback(data: Feedback):
    feedbacks.append(data.model_dump())
    return {"message": f"Спасибо, {data.name}! Ваш отзыв сохранён."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
