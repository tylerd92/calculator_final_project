from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/fastapi_db"
    TEST_DATABASE_URL: Optional[str] = None

    # JWT Configuration
    JWT_SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    JWT_REFRESH_SECRET_KEY: str = "your-refresh-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security Configuration
    BCRYPT_ROUNDS: int = 12
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]  # Restrict in production

    # Redis Configuration
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Application Settings
    APP_NAME: str = "Calculator API"
    VERSION: str = "1.0.0"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()