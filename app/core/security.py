# app/core/security.py
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
from typing import Dict, Any
from app.user.user_schema import TokenData
from jose.exceptions import JWSAlgorithmError
import secrets
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, status
import logging
import time
from typing import Any, Optional, Union
# Configure logging
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Google token verification


def verify_google_token(token: str) -> dict:
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        if idinfo['aud'] != settings.GOOGLE_CLIENT_ID:
            raise ValueError('Invalid audience')

        if idinfo['exp'] < time.time():
            raise ValueError('Expired token')

        return {
            'email': idinfo['email'],
            'email_verified': idinfo['email_verified'],
            'name': idinfo.get('name'),
            'given_name': idinfo.get('given_name'),
            'family_name': idinfo.get('family_name'),
            'picture': idinfo.get('picture'),
            'locale': idinfo.get('locale'),
            'sub': idinfo['sub']  # Google's unique user ID
        }
    except ValueError as e:
        logger.error(f"Invalid Google token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

# Internal token creation helper


def _create_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    try:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except JWSAlgorithmError as e:
        logger.error(f"Failed to encode JWT: {str(e)}")
        raise ValueError("Failed to encode JWT") from e

# Create access token with enriched payload


# def create_access_token(data: Dict[str, Any]) -> str:
#     """
#     Create an access token with user data embedded in the payload.

#     Args:
#         data: Dictionary containing user data (e.g., sub, email, roles).

#     Returns:
#         str: Encoded JWT access token.
#     """
#     if "sub" in data:
#         data["sub"] = str(data["sub"])  # Ensure sub is a string

#     to_encode = data.copy()
#     to_encode.update({
#         "token_type": "access",
#         "id": data.get("sub"),  # Optional: include subject ID
#         "email": data.get("email"),  # Optional: include email
#         "roles": data.get("roles", [])  # Optional: include roles
#     })
#     expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     return _create_token(to_encode, expires_delta=expires_delta)

# Create refresh token


# def create_refresh_token(data: Dict[str, Any]) -> str:
#     """
#     Create a refresh token with minimal payload.

#     Args:
#         data: Dictionary containing user data (e.g., sub).

#     Returns:
#         str: Encoded JWT refresh token.
#     """
#     if "sub" in data:
#         data["sub"] = str(data["sub"])  # Ensure sub is a string

#     to_encode = data.copy()
#     to_encode.update({"token_type": "refresh"})
#     expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
#     return _create_token(to_encode, expires_delta=expires_delta)

def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token with custom data payload.

    Args:
        data: Dictionary containing payload data (e.g., {"sub": "user_id", "email": "user@example.com"})
        expires_delta: Optional custom expiration time delta
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()  # Avoid modifying the input dict
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token with custom data payload.

    Args:
        data: Dictionary containing payload data (e.g., {"sub": "user_id", "email": "user@example.com"})
        expires_delta: Optional custom expiration time delta
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()  # Avoid modifying the input dict
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Verify access token and return enriched TokenData


def verify_access_token(token: str, credentials_exception: HTTPException) -> TokenData:
    try:
        logger.debug(f"Verifying token: {token[:20]}...")
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
        logger.debug(f"Token payload: {payload}")

        if payload.get("token_type") != "access":
            logger.warning(f"Invalid token type: {payload.get('token_type')}")
            raise credentials_exception

        user_id: str | None = payload.get("sub")
        if user_id is None:
            logger.warning("No subject ID in token")
            raise credentials_exception

        return TokenData(id=user_id, email=payload.get("email"))
    except JWTError as e:
        logger.error(f"JWT verification error: {str(e)}", exc_info=True)
        raise credentials_exception

# Verify refresh token


def verify_refresh_token(token: str, credentials_exception: HTTPException) -> TokenData:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=settings.ALGORITHM)
        if payload.get("token_type") != "refresh":
            logger.warning(f"Invalid token type: {payload.get('token_type')}")
            raise credentials_exception

        user_id: str | None = payload.get("sub")
        if user_id is None:
            logger.warning("No subject ID in token")
            raise credentials_exception

        return TokenData(id=user_id, email=payload.get("email"))
    except JWTError as e:
        logger.error(
            f"Refresh token verification error: {str(e)}", exc_info=True)
        raise credentials_exception

# Password utilities


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Token generation for verification/reset


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)
