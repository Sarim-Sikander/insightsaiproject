from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    class Config:
        case_sensitive = True


class Config(BaseConfig):
    HOST: str = "0.0.0.0"
    PORT: int = 5500
    ENVIRONMENT: str
    DATABASE_URL: str
    OPEN_AI_KEY: str

    class Config:
        env_file = "./.env.dev"


config: Config = Config()
