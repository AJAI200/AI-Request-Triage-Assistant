import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./triage.db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "node_solutions_jwt_secret_key_2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "1440"))
    API_KEY: str = os.getenv("API_KEY", "node_solutions_secret_key_123")

settings = Settings()
