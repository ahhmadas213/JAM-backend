from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.database.models.user import User as UserModel
from app.users.user_schema import UserCreate, UserUpdate
from app.core.security import get_password_hash
from app.database.database import get_db

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_in: UserCreate) -> UserModel:
        try:
            # Check if user exists
            query = select(UserModel).where(UserModel.email == user_in.email)
            result = await self.db.execute(query)
            existing_user = result.scalar_one_or_none()  # ✅ Fixed method name
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already exists"
                )
            # Create user with hashed password
            user = UserModel(
                email=user_in.email,
                username=user_in.username,
                password=get_password_hash(user_in.password)
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()  # Rollback on error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def get_by_id(self, user_id: int) -> Optional[UserModel]:
        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        try:
            query = select(UserModel).offset(skip).limit(limit)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Error in UserService.get_all: {e}")  # Add logging
            raise

    async def update(self, user_id: int, user_in: UserUpdate) -> UserModel:
        async with self.db.begin():
            user = await self.get_by_id(user_id)
            update_data = user_in.model_dump(exclude_unset=True)
            
            if 'email' in update_data:
                query = select(UserModel).where(UserModel.email == update_data['email'])
                result = await self.db.execute(query)
                if result.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already in use"
                    )

            if 'password' in update_data:
                update_data['password'] = get_password_hash(update_data['password'])

            for field, value in update_data.items():
                setattr(user, field, value)
                
            await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        await self.db.delete(user)
        await self.db.commit()  # ✅ Fixed syntax
