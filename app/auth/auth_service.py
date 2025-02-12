# app/users/auth_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.database.models.user import User  # Import User Model
from app.core.security import verify_password, get_password_hash
from app.users.user_schema import UserCreate, UserLogin # Import Schema
from sqlalchemy.exc import IntegrityError

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, user: UserCreate):
        try:
            # Check if user already exists (async)
            result = await self.db.execute(select(User).filter(User.email == user.email))
            existing_user = result.scalars().first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            hashed_password = get_password_hash(user.password)
            new_user = User(email=user.email, username=user.username, password=hashed_password)
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user) # Refresh after commit
            return new_user
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )


    async def authenticate_user(self, credentials: UserLogin):
    # Use async operations
        result = await self.db.execute(select(User).filter(User.email == credentials.email))
        user = result.scalars().first()

        if not user or not verify_password(credentials.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user