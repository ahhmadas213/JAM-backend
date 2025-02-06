# auth_router for user registration, login, and logout
from fastapi import APIRouter, Depends, Response, status, HTTPException, Cookie
from app.api.deps import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.users.user_schema import UserCreate, UserLogin, UserResponse
from app.auth.auth_service import AuthService
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models.user import User


router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    return await auth_service.register_user(user)

@router.post("/login")
async def login(
    response: Response,
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(credentials)
    
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    cookie_config = settings.COOKIE_CONFIG
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        **cookie_config
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=cookie_config.get("refresh_max_age"),
        httponly=cookie_config.get("httponly"),
        secure=cookie_config.get("secure"),
        samesite=cookie_config.get("samesite")
    )

    return {"message": "Login successful"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}

from fastapi import Cookie, HTTPException

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    access_token: str = Cookie(None),  # Extract access_token from cookies
    db: AsyncSession = Depends(get_db)
):  
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Decode the token to get the user's email
    try:
        decoded_token = decode_token(access_token)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    query = select(User).filter(User.email == decoded_token["sub"])
    result = await db.execute(query)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user