from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import Product, UserDB
from schemas import User, UserOut
from exceptions import CustomExceptionA, CustomExceptionB

Base.metadata.create_all(bind=engine)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


# Обработчик для CustomExceptionA
@app.exception_handler(CustomExceptionA)
async def exception_a_handler(request, exc):
    print(f"Error (CustomExceptionA): {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


# Обработчик для CustomExceptionB
@app.exception_handler(CustomExceptionB)
async def exception_b_handler(request, exc):
    print(f"Error (CustomExceptionB): {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


# Эндпоинт для проверки валидации данных пользователя (10.2)
@app.post("/users", response_model=UserOut, status_code=201)
def create_user(user: User, db: Session = Depends(get_db)):
    """
    Создание пользователя с валидацией по модели User
    (age > 18, email валиден, password 8-16 символов)
    """
    # Проверка на уникальность
    existing_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if existing_user:
        raise CustomExceptionA("Email already registered")

    db_user = UserDB(
        username=user.username,
        age=user.age,
        email=user.email,
        password=user.password,
        phone=user.phone or "Unknown"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Получение пользователя по ID (10.2, 11.1)
@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Получение пользователя. Выбрасывает CustomExceptionB если пользователь не найден.
    """
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise CustomExceptionB("User not found")
    return user


# Удаление пользователя по ID (10.2, 11.1)
@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Удаление пользователя. Выбрасывает CustomExceptionB если пользователь не найден.
    """
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise CustomExceptionB("User not found")
    db.delete(user)
    db.commit()
    return None


# Эндпоинт для демонстрации CustomExceptionA
@app.get("/check-condition/{condition}")
def check_condition(condition: str):
    """
    Демонстрация CustomExceptionA: если condition != 'ok', выбрасывает исключение
    """
    if condition != "ok":
        raise CustomExceptionA(f"Condition '{condition}' is not valid")
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
