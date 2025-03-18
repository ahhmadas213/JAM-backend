from pydantic import BaseModel, EmailStr
from typing import Union
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserResponse(BaseModel):
    name: str
    id: str
    email: EmailStr
    profile_image_url: Optional[str]


    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    email: Union[EmailStr, None] = None
    name: Union[str, None] = None
    profile_image_url: Union[str, None] = None
    class Config:
        from_attributes = True


class TokenData(BaseModel):
    id: Union[str, None] = None
    email: str | None = None  # Optional fields as needed
    roles: list[str] | None = None  # Example: for authorization


class AccountBase(BaseModel):
    provider: str
    provider_account_id: str


class AccountCreate(AccountBase):
    user_id: int


class Account(AccountBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: str
    name: str | None = None


class UserCreate(UserBase):
    password: Optional[str] = None


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


