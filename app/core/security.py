# app/core/security.py
from datetime import datetime, timedelta, timezone  # Import timezone
from jose import jwt, JWTError  # Import JWTError
from passlib.context import CryptContext
from app.core.config import settings
from typing import Dict, Any
from app.user.user_schema import TokenData
from jose.exceptions import JWSAlgorithmError
import secrets
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException
from app.core.config import settings
import time

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# utils/google.py


def verify_google_token(token: str) -> dict:
    try:
        # Verify the token using Google's client library
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        # Verify the token was issued for your application
        if idinfo['aud'] != settings.GOOGLE_CLIENT_ID:
            raise ValueError('Invalid audience')

        # Verify the token is not expired
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
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )


def _create_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    try:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except (JWSAlgorithmError) as e:
        # Log the error and/or raise a custom exception
        raise ValueError("Failed to encode JWT") from e


def create_access_token(data: Dict[str, Any]) -> str:
    # Make sure the subject (user id) is converted to string
    if "sub" in data:
        data["sub"] = str(data["sub"])  # Ensure sub is a string

    data = data.copy()
    data.update({"token_type": "access"})
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(data, expires_delta=expires_delta)


def create_refresh_token(data: Dict[str, Any]) -> str:
    # Make sure the subject (user id) is converted to string
    if "sub" in data:
        data["sub"] = str(data["sub"])  # Ensure sub is a string

    data = data.copy()
    data.update({"token_type": "refresh"})
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(data, expires_delta=expires_delta)


def verify_access_token(token: str, credentials_exception):
    try:
        print(f"Verifying token: {token[:20]}...")

        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
        print(f"Token payload: {payload}")

        if payload.get("token_type") != "access":
            print(f"Invalid token type: {payload.get('token_type')}")
            raise credentials_exception

        id: str = str(payload.get("sub"))  # Ensure it's a string
        print(f"Token subject ID: {id}, Type: {type(id)}")

        if id is None:
            print("No subject ID in token")
            raise credentials_exception

        # Try converting to int to validate format
        try:
            int(id)
        except ValueError:
            print(f"Invalid ID format: {id}")
            raise credentials_exception

        return TokenData(id=id)
    except JWTError as e:
        print(f"JWT verification error: {str(e)}")
        print(f"Token that caused error: {token[:20]}...")
        raise credentials_exception

# security


def verify_refresh_token(token: str, credentials_exception):
    try:
        # Use REFRESH_TOKEN_SECRET_KEY
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=settings.ALGORITHM)

        # Check if it's a refresh token
        if payload.get("token_type") != "refresh":
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        return TokenData(id=user_id)  # Return TokenData

    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    except Exception:
        raise credentials_exception


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_verification_token():
    return secrets.token_urlsafe(32)


def generate_password_reset_token():
    return secrets.token_urlsafe(32)
