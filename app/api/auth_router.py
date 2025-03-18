# auth_router for user registration, login, and logout
import os
from app.database.models.user import User as UserModel
from app.database.models.user import Account
from fastapi import Depends, HTTPException, status, Response, Request, Cookie, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.user.user_schema import UserCreate, UserLogin, UserResponse
from app.auth.auth_service import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings
from fastapi.responses import RedirectResponse, JSONResponse
import logging
from fastapi.security import OAuth2PasswordBearer  # Import OAuth2PasswordBearer
# Alias to avoid confusion
from jose import JWTError, jwt
from starlette.config import Config
from app.user.user_repository import UserRepository
from app.dependencies import get_current_user
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid input data"},
        409: {"description": "Conflict with existing resource"},
        503: {"description": "Service unavailable"}
    }
)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    try:
        auth_service = AuthService(db)
        response = await auth_service.create_user(user)
        return response
    except HTTPException as e:
        raise  # Propagate HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Unexpected error in register endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "server_error",
                "message": "An unexpected error occurred during registration",
                "field": None
            }
        )


@router.post(
    "/signin",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successful authentication"},
        401: {"description": "Authentication failed"},
        403: {"description": "Forbidden - email not verified"},
        500: {"description": "Server error"}
    }
)
async def sign_in(
    credentials: UserLogin,
    response: Response,  # Add Response parameter
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        auth_service = AuthService(db)
        user = await auth_service.signin(credentials)

        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email})

        # Set the refresh token in an HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # Required for samesite="none"
            samesite="none",  # Allows cross-origin requests
            max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
            path="/",
        )

        return {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
            }
        }
    except HTTPException as e:
        raise  # Propagate HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Unexpected error in signin endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "server_error",
                "message": "An unexpected error occurred during sign-in processing",
                "field": None
            }
        )


@router.get("/login/google")
async def login_google(request: Request):
    # Ensure this matches your callback route
    redirect_uri = str(request.url_for("oauth_callback"))
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=["openid", "email", "profile"],
        redirect_uri=redirect_uri
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )
    response = RedirectResponse(url=authorization_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        path="/api/auth",
        secure=False,  # Use secure=True in production with HTTPS
        samesite="lax"
    )
    return response


@router.get("/callback/google", name="oauth_callback")
async def oauth_callback(request: Request, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    state_from_cookie = request.cookies.get("oauth_state")
    state_from_query = request.query_params.get("state")
    print(
        f"Cookie state: {state_from_cookie}, Query state: {state_from_query}")
    if not state_from_cookie or state_from_cookie != state_from_query:
        raise HTTPException(
            status_code=400, detail="State mismatch or missing")

    redirect_uri = str(request.url_for("oauth_callback"))
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=["openid", "email", "profile"],
        redirect_uri=redirect_uri
    )
    flow.state = state_from_query

    if os.getenv("ENVIRONMENT", "development") == "development":
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

    authorization_response = str(request.url)
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials

    id_info = id_token.verify_oauth2_token(
        credentials.id_token,
        GoogleRequest(),
        settings.GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=10
    )

    email = id_info.get("email")
    if not email:
        raise HTTPException(
            status_code=400, detail="No email provided by Google")

    # Check if user exists
    try:
        user = await user_repo.get_user_by_email(email)
    except ValueError:
        user = None

    # Check if OAuth account exists
    provider_account_id = id_info.get("sub")
    account = await user_repo.get_account_by_provider(provider_account_id, provider="google")

    if account and not user:
        user = await user_repo.get_user_from_account(account)

    # Create user if not exists
    if not user:
        name = id_info.get("name", "")
        user = UserModel(
            email=email,
            name=name,
            profile_image_url=id_info.get("picture"),
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Create or update OAuth account
    if not account:
        account = Account(
            user_id=user.id,
            provider="google",
            provider_account_id=provider_account_id,
            access_token=credentials.token,
            expires_at=credentials.expiry,
            refresh_token=credentials.refresh_token,
            token_data=credentials.to_json()
        )
        db.add(account)
    else:
        account.access_token = credentials.token
        account.refresh_token = credentials.refresh_token
        account.expires_at = credentials.expiry
        account.token_data = credentials.to_json()

    await db.commit()

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email})
    response = RedirectResponse(
        url=f"{settings.FRONTEND_URL}/auth/callback?token={access_token}")

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # Required for samesite="none"
        samesite="none",  # Allows cross-origin requests
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path="/",
    )
    return response


@router.post("/refresh")
async def refresh_token_endpoint(
    response: Response,
    request: Request,
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh an access token using a refresh token from a cookie.

    """

    refresh_token_test = request.cookies.get("session")

    print("Received cookies:", request.cookies)
    print("Refresh token:", refresh_token)
    print("this refresh token", refresh_token)
    print("this refrshtoken test", refresh_token_test)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    try:
        # Decode the refresh token
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Fetch user from database
        user_repo = UserRepository(db)
        user = await user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Create new tokens
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(data=token_data)
        new_refresh_token = create_refresh_token(data=token_data)

        # Set new refresh token in cookie
        # response.set_cookie(
        #     key="refresh_token",
        #     value=new_refresh_token,
        #     httponly=True,
        #     secure=False,  # Set to True in production
        #     samesite="lax",
        #     max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        #     path="/",
        #     domain="localhost"
        # )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "profile_image_url": user.profile_image_url
            }
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.get("/test-cookies")
async def test_cookies(request: Request):
    print("Cookies received:", request.cookies)
    return {"cookies": request.cookies}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="refresh_token", path="/auth")
    return {"message": "Successfully logged out"}


@router.get("/me")
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """
    Get details of the currently authenticated user.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "is_active": current_user.is_active,
        "profile_image_url": current_user.profile_image_url
    }
