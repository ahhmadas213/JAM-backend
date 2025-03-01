from pydantic import BaseModel, EmailStr
from typing import Union
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    is_verified: bool

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    email: Union[EmailStr, None] = None
    username: Union[str, None] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Union[str, None] = None


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
    username: str | None = None


class UserCreate(UserBase):
    password: Optional[str] = None


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    accounts: List[Account]

    class Config:
        from_attributes = True


class OAuthUser(BaseModel):
    provider: str
    providerAccountId: str
    name: str
    email: EmailStr
    profileImageUrl: Optional[str]
    id_token: str
