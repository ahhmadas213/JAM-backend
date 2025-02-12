# auth_router for user registration, login, and logout
from fastapi import APIRouter, Depends, Response, Request, status, HTTPException, Cookie
from app.database.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.users.user_schema import UserCreate, UserLogin, UserResponse, Token
from app.auth.auth_service import AuthService
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.user import User
from app.dependencies import get_current_user
from app.users.users_service import UserService

router = APIRouter()


@router.post("/signup", response_model=UserResponse)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    return await auth_service.register_user(user)


@router.post("/signin")
async def sign_in(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_service = UserService(db)
        # Authenticate user and generate token
        token = await user_service.signin(credentials)
        return token  # Return the token as a response
    # except HTTPException as e:
    #     # Re-raise HTTPException to return the same error response
    #     raise e
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# Add to auth_router.py


# Add to FastAPI implementation
# @router.post("/refresh")
# async def refresh_token(
#     request: Request,
#     response: Response,
#     db: AsyncSession = Depends(get_db)
# ):
#     refresh_token = request.cookies.get("refresh_token")
#     if not refresh_token:
#         raise HTTPException(status_code=401, detail="Missing refresh token")

#     try:
#         payload = decode_token(refresh_token)
#     except HTTPException:
#         raise HTTPException(
#             status_code=401, detail="Invalid/expired refresh token")

#     # Token rotation implementation
#     auth_service = AuthService(db)
#     user = await auth_service.get_user_by_email(payload["sub"])

#     if not user or user.refresh_token != refresh_token:
#         raise HTTPException(status_code=401, detail="Invalid refresh token")

#     # Generate new tokens
#     new_access_token = create_access_token({"sub": user.email})
#     new_refresh_token = create_refresh_token({"sub": user.email})

#     # Update user's refresh token in DB
#     user.refresh_token = new_refresh_token
#     await db.commit()

#     # Set new cookies
#     response.set_cookie(
#         key="access_token",
#         value=new_access_token,
#         **settings.COOKIE_CONFIG
#     )
#     response.set_cookie(
#         key="refresh_token",
#         value=new_refresh_token,
#         **settings.REFRESH_COOKIE_CONFIG
#     )

#     return {"message": "Tokens refreshed"}


# @router.post("/logout")
# async def logout(response: Response):
#     response.delete_cookie("access_token")
#     response.delete_cookie("refresh_token")
#     return {"message": "Logged out"}


# @router.get("/me", response_model=UserResponse)
# async def get_current_user(
#     db: AsyncSession = Depends(get_db),
#     current_user : User = Depends(get_current_user)
#     ):

    # if not access_token:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Not authenticated"
    #     )

    # # Decode the token to get the user's email
    # try:
    #     decoded_token = decode_token(access_token)
    # except HTTPException as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid or expired token"
    #     )

    # query = select(User).filter(User.email == decoded_token["sub"])
    # result = await db.execute(query)
    # user = result.scalars().first()

    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found"
    #     )

    # return {

    # }
