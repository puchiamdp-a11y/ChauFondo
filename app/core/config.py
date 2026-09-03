import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/chaufondo_db"
    JWT_SECRET: str = "your-secret-key-here-min-32-characters-long"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 168
    ENVIRONMENT: str = "development"
    MERCADO_PAGO_TOKEN: str = ""
    MERCADO_PAGO_SECRET: str = ""
    MERCADO_PAGO_PUBLIC_KEY: str = ""
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_IMAGE_FORMATS: str = "jpg,jpeg,png,webp"
    REMBG_TIMEOUT_SECONDS: int = 20
    REMBG_MODEL: str = "u2net"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
