from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    name: str
    age: int
    email: EmailStr

class UpdateUser(BaseModel):
    name: Optional[str]
    age: Optional[int]
    email: Optional[EmailStr]