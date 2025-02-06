# # app/api/routers/users.py
# from typing import List
# from fastapi import APIRouter, Depends, status, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.database.database import get_db
# from app.users.user_schema import User, UserCreate, UserUpdate
# from app.users.users_service import UserService

# router = APIRouter(tags=["users"], prefix="/users")


# @router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
# async def create_user(
#     user_in: UserCreate,
#     db: AsyncSession = Depends(get_db),
# ) -> User:
#     """
#     Create new user.
#     """
#     try:
#         user_service = UserService(db)
#         return await user_service.create(user_in)
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )


# @router.get("/", response_model=List[User])
# async def read_users(
#     skip: int = 0,
#     limit: int = 100,
#     db: AsyncSession = Depends(get_db),
# ) -> List[User]:
#     """
#     Retrieve users.
#     """
#     user_service = UserService(db)
#     return await user_service.get_all(skip=skip, limit=limit)


# @router.get("/{user_id}", response_model=User)
# async def read_user(
#     user_id: int,
#     db: AsyncSession = Depends(get_db),
# ) -> User:
#     """
#     Get user by ID.
#     """
#     user_service = UserService(db)
#     return await user_service.get_by_id(user_id)


# @router.put("/{user_id}", response_model=User)
# async def update_user(
#     user_id: int,
#     user_in: UserUpdate,
#     db: AsyncSession = Depends(get_db),
# ) -> User:
#     """
#     Update user.
#     """
#     try:
#         user_service = UserService(db)
#         return await user_service.update(user_id, user_in)
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )


# @router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_user(
#     user_id: int,
#     db: AsyncSession = Depends(get_db),
# ) -> None:
#     """
#     Delete user.
#     """
#     user_service = UserService(db)
#     await user_service.delete(user_id)
