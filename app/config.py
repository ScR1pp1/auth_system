import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
import secrets

class Settings(BaseSettings):
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    ALGORITHM: str = "HS256"
    SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    model_config = {
        'env_file': Path(__file__).parent.parent / '.env',
        'env_file_encoding': 'utf-8'
    }

    def get_db_url(self):
        return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")

settings = Settings()