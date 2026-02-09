import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./expense_tracker.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    HOLIDAY_API_PROVIDER: str = os.getenv("HOLIDAY_API_PROVIDER", "calendarific")
    CALENDARIFIC_API_KEY: str = os.getenv("CALENDARIFIC_API_KEY", "")

settings = Settings()
