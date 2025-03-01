from sqlalchemy.ext.asyncio import AsyncSession
# from app.auth.auth_schema import UserCreate, UserLogin
from app.user.user_schema import UserCreate, UserLogin
from app.user.user_repository import UserRepository
from fastapi import HTTPException, status
from app.core.security import get_password_hash, generate_verification_token, generate_password_reset_token
from app.database.models import User
from datetime import datetime, timedelta, timezone  # Import timezone
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_refresh_token, verify_password
import logging
from jose import jwt, JWTError


logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repository = UserRepository(db)

    async def create_user(self, user_in: UserCreate) -> User:
        try:
            existing_user = await self.user_repository.user_exist_by_email(user_in.email)
            if existing_user:
                raise HTTPException(
                    # More specific status code
                    status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

            hashed_password = get_password_hash(user_in.password)
            # verification_token = generate_verification_token()

            new_user = User(
                email=user_in.email,
                username=user_in.username,
                hashed_password=hashed_password,
            )

            response = await self.user_repository.create_user(new_user)

            # TODO
            # Send verification email
            # await self.send_verification_email(new_user.email, verification_token)
            # await send_verification_email(user.email, verification_token)

            return response
        except ValueError as ve:
            # Catch ValueErrors from the repository and convert to HTTPExceptions
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except Exception as e:
            logger.exception(
                "An unexpected error occurred during user creation: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"  # Don't expose internal error details
            )

    async def login(self, user_in: UserLogin):
        try:
            user = await self.user_repository.get_user_by_email(user_in.email)
            # No need to check for `not user` here, as get_user_by_email will raise a ValueError.

            # TODO remember to uncommited this for email verification
            # if not user.is_verified:
            #     raise HTTPException(
            #         status_code=400, detail="Email not verified")

            if not verify_password(user_in.password, user.hashed_password):
                raise HTTPException(
                    # 401 for auth failure
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

            access_token = create_access_token(
                data={"sub": str(user.id)})  # Ensure string ID
            refresh_token = create_refresh_token(data={"sub": str(user.id)})

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "token_type": "bearer",
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "id": str(user.id),
                    "profile_image_url": user.profile_image_url
                }
            }
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except HTTPException as e:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            logger.exception(
                "An unexpected error occurred during login: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    async def verify_user(self, token: str):
        try:
            user = await self.user_repository.get_user_by_verification_token(token)
            # No `if not user` check needed, get_user_by_verification_token raises

            if user.verification_token_expires < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token expired")

            # Convert user.id to string
            if await self.user_repository.verify_user(str(user.id)):
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": "Email verified successfully"
                }
            else:  # This is unlikely, but kept for consistency
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to verify email")
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except HTTPException as e:  # Catch existing HTTPExceptions
            raise
        except Exception as e:
            logger.exception(
                "An unexpected error occurred during user verification: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    async def send_verification_email(self, email: str, token: str):
        # TODO implment Resnd integration

        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        # TODO use Resned here

        pass

    # auth service

    # Add this to your auth_service.py file:

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh the access token using a valid refresh token.
        """
        try:
            # Verify the refresh token
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )

            # Extract user ID from token payload
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )

            # Convert user_id to UUID (if necessary) and get the user
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Create new tokens
            user_id_str = str(user.id)
            access_token = create_access_token(data={"sub": user_id_str})
            new_refresh_token = create_refresh_token(data={"sub": user_id_str})

            # Return tokens and user data
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
            }

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        except Exception as e:
            logger.exception("Error refreshing token: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not refresh token"
            )
