from pydantic import BaseModel, ConfigDict, conint, constr, EmailStr
from typing import Optional


class User(BaseModel):
    username: str
    age: conint(gt=18)
    email: EmailStr
    password: constr(min_length=8, max_length=16)
    phone: Optional[str] = "Unknown"


class UserOut(BaseModel):
    id: int
    username: str
    age: int
    email: str
    phone: str

    model_config = ConfigDict(from_attributes=True)
