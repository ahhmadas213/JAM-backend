from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key"  # Use env var in production
ALGORITHM = "HS256"
ACCESS_EXPIRE = timedelta(minutes=15)
REFRESH_EXPIRE = timedelta(days=7)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_tokens(data: dict):
    access_token = create_token(data, ACCESS_EXPIRE)
    refresh_token = create_token(data, REFRESH_EXPIRE)
    return access_token, refresh_token

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)