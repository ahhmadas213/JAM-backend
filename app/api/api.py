from fastapi import APIRouter
from .auth_router import router as auth_router
from .user_router import router as users_router
from app.core.config import settings

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/user", tags=["User"])

# Change from empty string to "/"


@api_router.get("/")
async def root():
    return {
        "message": "Welcome",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    }
