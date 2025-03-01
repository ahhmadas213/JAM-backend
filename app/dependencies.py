from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import verify_access_token
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.user.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='api/auth/signin')


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_data = verify_access_token(token, credentials_exception)
        user_repository = UserRepository(db)

        try:
            user = await user_repository.get_user_by_id(token_data.id)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return user
        except ValueError as e:
            print(f"Value error in get_current_user: {e}")
            raise credentials_exception
        except Exception as e:
            print(f"Error in get_current_user: {e}")
            raise credentials_exception

    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise credentials_exception
