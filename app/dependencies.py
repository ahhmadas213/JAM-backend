# app/dependencies.py
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.database.models.user import User  # Import User
from app.database.database import get_db, engine
from app.database.models import Base
from sqlalchemy import select
from fastapi.security import OAuth2PasswordBearer
from app.core.security import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='signin')


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    return verify_access_token(token, credentials_exception)


async def create_tables():
    async with engine.begin() as conn:
        # for droping and recreate the tables.
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
