# auth_router for user registration, login, and logout
from app.database.models.user import User as UserModel
from fastapi import APIRouter, Depends, status, HTTPException
from app.database.database import get_db
from app.user.user_schema import UserCreate, UserLogin, UserResponse,  AccountCreate
from app.auth.auth_service import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from app.user.user_repository import UserRepository
from app.core.security import create_access_token, create_refresh_token
from authlib.integrations.starlette_client import OAuth  # Use Authlib
from app.core.config import settings
from fastapi.responses import RedirectResponse
import logging
from fastapi.security import OAuth2PasswordBearer  # Import OAuth2PasswordBearer
from typing import Annotated
from app.user.user_schema import OAuthUser
from google.oauth2 import id_token
# Alias to avoid confusion
from google.auth.transport.requests import Request as GoogleRequest
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["Authentication"])

# Use a dummy endpoint, as it is for dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        auth_service = AuthService(db)
        response = await auth_service.create_user(user)
        return response
    except HTTPException as e:  # Catch HTTPErrors directly
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred"  # Do not expose internal errors
        )


@router.post("/signin", status_code=status.HTTP_200_OK)
async def sign_in(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    try:
        auth_service = AuthService(db)
        response = await auth_service.login(credentials)
        return response

    except HTTPException as e:  # Catch HTTPErrors from the service
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/oauth")
async def google_callback(accountCreate: OAuthUser, db: AsyncSession = Depends(get_db)):

    try:
        user_repo = UserRepository(db)

        # Verify Google ID token
        request = GoogleRequest()
        try:
            idinfo = id_token.verify_oauth2_token(
                accountCreate.id_token,
                request,
                settings.GOOGLE_CLIENT_ID  # Ensure token was meant for your app
            )

            # Optional: check if email in token matches email in request payload
            if idinfo.get("email") != accountCreate.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email mismatch between ID token and request payload"
                )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google ID token"
            ) from e

        # Check if user exists
        user_exists = await user_repo.user_exist_by_email(accountCreate.email)

        if user_exists:
            user = await user_repo.get_user_by_email(accountCreate.email)
            logger.info(f"User exists - user.id: {user.id}")

            account = await user_repo.get_account_by_provider(user.id, accountCreate.provider)

            if not account:
                # Create account for existing user
                account_data = AccountCreate(
                    user_id=user.id,
                    provider=accountCreate.provider,
                    provider_account_id=accountCreate.providerAccountId,
                )
                await user_repo.create_account(account_data)

        else:
            # Create new user and account
            new_user = UserModel(
                email=accountCreate.email,
                username=accountCreate.name,
                profile_image_url=accountCreate.profileImageUrl,
                hashed_password=None
            )
            user = await user_repo.create_user(new_user)

            account_data = AccountCreate(
                user_id=user.id,
                provider=accountCreate.provider,
                provider_account_id=accountCreate.providerAccountId,
            )
            await user_repo.create_account(account_data)

        # Create tokens for the user (whether newly created or existing)
        user_id_str = str(user.id)
        access_token = create_access_token(data={"sub": user_id_str})
        refresh_token = create_refresh_token(data={"sub": user_id_str})

        # Successful login response
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    except ValueError as ve:
        logger.error(f"Value error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        ) from ve

    except HTTPException as he:
        logger.error(f"HTTP error: {he}")
        raise

    except Exception as e:
        logger.exception("An unexpected error occurred: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Updated refresh endpoint for auth_router.py


@router.post("/refresh")
async def refresh_token(token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)):
    try:
        auth_service = AuthService(db)
        refreshed_token_info = await auth_service.refresh_token(token)
        # Ensure refreshed_token_info includes expires_in
        return {
            "access_token": refreshed_token_info["access_token"],
            "refresh_token": refreshed_token_info.get("refresh_token", token),  # Use new token if provided
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except HTTPException as e:
        raise
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", e)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")