from fastapi import HTTPException, status
from app.user.user_schema import UserUpdate
from app.user.user_repository import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession

class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repository = UserRepository(db)

    async def get_user_by_id(self, user_id: str):
        try:
            return await self.user_repository.get_user_by_id(user_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {str(e)}"
            )

    async def update_user(self, user_id: str, user_update: UserUpdate):
        try:
            return await self.user_repository.update_user(user_id, user_update.dict(exclude_unset=True))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user: {str(e)}"
            )

    async def delete_user(self, user_id: str):
        try:
            return await self.user_repository.delete_user(user_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete user: {str(e)}"
            )