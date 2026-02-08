from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://scrooge:scrooge_secret@localhost:5432/scrooge_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    SECRET_KEY: str = "change-me-to-a-random-secret-key-at-least-32-chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Admin
    ADMIN_INVITE_CODE: str = "SCROOGE-ADMIN-2024"

    # Steam
    STEAM_API_KEY: str = ""

    # Scraper
    SCRAPE_INTERVAL_MINUTES: int = 30
    MAX_CONCURRENT_SCRAPERS: int = 5
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Proxy
    PROXY_URL: str = ""
    PROXY_ROTATION_ENABLED: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
