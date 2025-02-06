# auth_service for user registration and authentication

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.database.models.user import User
from app.core.security import verify_password, get_password_hash
from app.users.user_schema import UserCreate, UserLogin

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, user: UserCreate):
        query = select(User).filter(User.email == user.email)
        result = await self.db.execute(query)
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
        await self.db.refresh(new_user)
        return new_user

    async def authenticate_user(self, credentials: UserLogin):
        query = select(User).filter(User.email == credentials.email)
        result = await self.db.execute(query)
        user = result.scalars().first()
        
        if not user or not verify_password(credentials.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user