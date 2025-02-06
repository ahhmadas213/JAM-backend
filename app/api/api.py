# Purpose: Define the API router and include module-specific routers.
from fastapi import APIRouter
# from ..users.users_router import router as users_router
from ..auth.auth_router import router as auth_router

api_router = APIRouter(prefix="/api", tags=["API"])

# api_router.include_router(users_router)
api_router.include_router(auth_router)


@api_router.get("")
async def root():
    return {
        "message": "Welcome",
        "version": "1.0.0",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    }
