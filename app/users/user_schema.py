from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

from pydantic import UUID4

class UserResponse(BaseModel):
    id: UUID4
    email: EmailStr
    username: str

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str