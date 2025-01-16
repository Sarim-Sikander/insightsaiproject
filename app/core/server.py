from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import router
from app.core.config import config
from app.core.database.create_db import validate_database
from app.core.middlewares.sqlalchemy import SQLAlchemyMiddleware


def init_db():
    validate_database()


def init_routers(app_: FastAPI) -> None:
    app_.include_router(router)


def create_app() -> FastAPI:
    app_ = FastAPI(
        title="LLms Project API",
        description="Dashboard",
        version="1.0.0",
        docs_url=None if config.ENVIRONMENT == "production" else "/docs",
        redoc_url=None if config.ENVIRONMENT == "production" else "/redoc",
    )

    app_.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app_.add_middleware(SQLAlchemyMiddleware)
    init_routers(app_=app_)
    return app_


app = create_app()
