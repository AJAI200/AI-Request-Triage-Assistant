import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "")
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "1440"))
    API_KEY: str = os.getenv("API_KEY", "")

settings = Settings()
