import re

from pydantic import BaseModel, Field, field_validator


# Задание 1.4 — User с name и id
class User(BaseModel):
    name: str
    id: int


# Задание 1.3 — входные данные для /calculate
class CalculateRequest(BaseModel):
    num1: float
    num2: float


# Задание 1.5 — User с name и age
class UserWithAge(BaseModel):
    name: str
    age: int


# Задание 2.1 + 2.2 — Feedback с валидацией
class Feedback(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    message: str = Field(min_length=10, max_length=500)

    @field_validator("message")
    @classmethod
    def check_bad_words(cls, v: str) -> str:
        bad_words = ["кринж", "рофл", "вайб"]
        lower = v.lower()
        for word in bad_words:
            if re.search(word, lower):
                raise ValueError("Использование недопустимых слов")
        return v
