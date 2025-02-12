from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.database.models.user import User as UserModel
from app.users.user_schema import UserCreate, UserUpdate, UserResponse, UserLogin
from app.core.security import get_password_hash
from app.database.database import get_db
from app.users.users_repository import UserRepository
from app.core.security import get_password_hash, verify_password, create_access_token


class UserService:
    def __init__(self, db: AsyncSession):
        self.__UserRepository = UserRepository(db)

    async def signup(self, user_in: UserCreate) -> UserResponse:
        try:
            if await self.__UserRepository.user_exist_by_email(user_in.email):
                return HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="this email alredy exist pleas signin"
                )

            hashed_password = get_password_hash(user_in.password)
            user_in.password = hashed_password
            return await self.__UserRepository.create(user_in)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def signin(self, user_in: UserLogin):
        try:
            # Check if the user exists by email
            if not await self.__UserRepository.user_exist_by_email(user_in.email):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            # Retrieve the user by email
            user = await self.__UserRepository.get_user_by_email(user_in.email)

            # Verify the password
            if not verify_password(user_in.password, user.password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            # Create an access token
            access_token = create_access_token({"user_id": str(user.id)})

            # Return the access token
            return {"access_token": access_token, "token_type": "bearer"}

        except Exception as e:
            raise e
