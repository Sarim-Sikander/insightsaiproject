import uvicorn

from app.core.config import config


def run():
    uvicorn.run(
        app="app.core.server:app",
        host=config.HOST,
        port=config.PORT,
        reload=True if config.ENVIRONMENT != "production" else False,
        workers=1,
    )
