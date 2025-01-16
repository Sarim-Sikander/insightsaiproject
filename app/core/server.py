from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import router  # Import the API router for endpoints.
from app.core.config import config  # Import configuration settings.
from app.core.database.create_db import validate_database  # Function to validate the database.
from app.core.middlewares.sqlalchemy import SQLAlchemyMiddleware  # Middleware for SQLAlchemy.


def init_db():
    """
    Initialize and validate the database.
    - Ensures the database is properly set up before the application starts.
    """
    validate_database()


def init_routers(app_: FastAPI) -> None:
    """
    Include API routers in the FastAPI application.
    - Adds the main API router for endpoint registration.
    """
    app_.include_router(router)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    - Sets up middleware, routing, and environment-specific settings.
    """
    app_ = FastAPI(
        title="LLms Project API",  # Title of the API.
        description="Dashboard",  # Description for the API documentation.
        version="1.0.0",  # Version of the API.
        docs_url=None if config.ENVIRONMENT == "production" else "/docs",  # Disable docs in production.
        redoc_url=None if config.ENVIRONMENT == "production" else "/redoc",  # Disable Redoc in production.
    )

    # Add CORS middleware to allow cross-origin requests.
    app_.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins.
        allow_credentials=True,  # Allow credentials (cookies, headers, etc.).
        allow_methods=["*"],  # Allow all HTTP methods.
        allow_headers=["*"],  # Allow all headers.
    )

    # Add SQLAlchemy middleware for database session management.
    app_.add_middleware(SQLAlchemyMiddleware)

    # Initialize API routers.
    init_routers(app_=app_)
    return app_  # Return the configured FastAPI application instance.


# Create the FastAPI application instance.
app = create_app()
