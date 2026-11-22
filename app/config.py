import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:  # python-dotenv is optional at import time
    pass


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'health.db'}")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-only-insecure-key-change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    FRONTEND_DIR: Path = BASE_DIR / "frontend"


settings = Settings()
