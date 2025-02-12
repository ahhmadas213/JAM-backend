# app/core/security.py
from datetime import datetime, timedelta, timezone  # Import timezone
from jose import jwt, JWTError  # Import JWTError
from passlib.context import CryptContext
from app.core.config import settings
from typing import Dict, Any
from app.users.user_schema import TokenData
from jose.exceptions import JWSAlgorithmError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    exires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(
        data,
        expires_delta=exires_delta,

    )


def create_refresh_token(data: Dict[str, Any]) -> str:

    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(
        data,
        expires_delta=expires_delta,
    )


def verify_access_token(token: str, credentials_exception):

    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                            algorithms=[settings.ALGORITHM])

        id: str = payload.get("user_id")
        if id is None:
            raise credentials_exception

        token_data = TokenData(id=id)

    except JWTError:
        raise credentials_exception

    return token_data


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# def decode_token(token: str) -> Dict[str, Any]:  #  <-- Specify return type
#     try:
#         # *Now* decode and verify.
#         payload = jwt.decode(
#             token,
#             settings.SECRET_KEY,
#             algorithms=[settings.ALGORITHM]
#         )

#         return payload #return the payload
#     except JWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials", # Changed the detail message
#             headers={"WWW-Authenticate": "Bearer"},
#         )
