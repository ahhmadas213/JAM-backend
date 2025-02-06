from typing import Annotated, AsyncGenerator
from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.core.security import decode_token
from app.database.models.user import User
from sqlalchemy.future import select

async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    access_token: Annotated[str | None, Cookie()] = None,
    refresh_token: Annotated[str | None, Cookie()] = None
):
    if not access_token:
        if refresh_token:
            # Implement refresh token logic here if needed
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        payload = decode_token(access_token)
        result = await db.execute(select(User).filter(User.email == payload["sub"]))
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        return user
    except HTTPException as e:
        raise e