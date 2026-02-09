import os


class Settings:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "scrooge.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
    SECRET_KEY = "scrooge-local-secret-key-2024-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 30
    ALGORITHM = "HS256"
    ADMIN_INVITE_CODE = "SCROOGE-ADMIN-2024"
    STEAM_API_KEY = ""
    SCRAPE_INTERVAL_MINUTES = 30
    MAX_CONCURRENT_SCRAPERS = 1
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    PROXY_URL = ""
    PROXY_ROTATION_ENABLED = False


settings = Settings()
