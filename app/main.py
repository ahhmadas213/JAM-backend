# main.py file

# Standard library imports
from contextlib import asynccontextmanager

# Third-party imports
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import run

# Local application imports
from app.api.api import api_router
from app.auth.auth_router import router as auth_router
from app.core.config import settings
from app.database.database import engine
from app.database.models.base import Base as ModelBase

load_dotenv(".env")  # Load environment variables from .env file


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)
    print("Tables created...")

    yield  # Server is running and handling requests

    # Shutdown
    print("Shutting down...")
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Your project description",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost",
    "http://localhost:3000",  # React default port
    "http://localhost:8000",  # FastAPI default port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
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
