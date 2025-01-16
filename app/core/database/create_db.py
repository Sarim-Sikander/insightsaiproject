from sqlalchemy import create_engine
from sqlalchemy_utils.functions import create_database, database_exists

from app.core.config import config


def validate_database():
    engine = create_engine(config.DATABASE_URL)

    if database_exists(engine.url):
        print("Database already exists")
    else:
        # Create a new database
        create_database(engine.url)
        print("New database created")
