from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./cinema.db"
    PROJECT_NAME: str = "HomeRezka-API"
    VERSION: str = "0.0.1"
    DESCRIPTION: str = "HomeRezka-API"
    MAIN_PAGE_URL: str = "https://rezka.ag"
    SEARCH_URL_BASE: str = "https://rezka.ag/search/?do=search&subaction=search&q="

    class Config:
        case_sensitive = True


settings = Settings()
