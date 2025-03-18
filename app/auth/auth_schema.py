from pydantic import BaseModel, EmailStr

from typing import Optional
from pydantic import BaseModel, field_validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class VerificationRequest(BaseModel):
    token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[int] = None
    type: Optional[str] = None

    @field_validator
    def validate_token_type(cls, v):
        if v not in ["access", "refresh"]:
            raise ValueError("Token type must be 'access' or 'refresh'")
        return v