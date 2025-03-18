# main.py

# Standard library imports
import secrets
from app.database.models.base import Base as ModelBase
from app.database.database import engine
from app.core.config import settings
from app.api.auth_router import router as auth_router
from app.api.api import api_router
from uvicorn import run
from starlette.middleware.sessions import SessionMiddleware  # Ensure this is imported
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
import logging
from app.core.config import settings

# Third-party imports
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv(".env")  # Load environment variables from .env file


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.debug("Starting up...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(ModelBase.metadata.create_all)
        logger.debug("Tables created...")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

    yield  # Server is running and handling requests

    # Shutdown
    logger.debug("Shutting down...")
    await engine.dispose()

# Generate a secure secret key for session middleware
secret_key = secrets.token_hex(32)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Your project description",
    version="1.0.0",
    lifespan=lifespan,
    root_path=settings.API_PREFIX
)

# Add SessionMiddleware

# Add CORS middleware


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    # secure=False,
    path="/api/auth",
)
origins = [
    "https://localhost:3000",  # Your Next.js frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Must be True to allow cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(api_router)

if __name__ == "__main__":
    run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS_COUNT,
        log_level="debug"
    )
