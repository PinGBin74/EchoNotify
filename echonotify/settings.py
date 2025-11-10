import json
import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    DB_HOST: str = ""
    DB_PORT: int = 0
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_DRIVER: str = ""
    DB_NAME: str = ""
    DATABASE_URL: str = ""
    CORS_ORIGINS: str = ""
    CORS_MAX_AGE: int = ""

    # JWT settings
    JWT_SECRET_KEY: str = ""
    JWT_ENCODE_ALGORITHM: str = ""

    # PyOTP settings
    PYOTP_SECRET_KEY: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Parse CORS_ORIGINS env var into a list of strings.
        """
        v = (self.CORS_ORIGINS or "").strip()
        if not v:
            return []
        if v.startswith("["):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except json.JSONDecodeError:
                pass
        return [x.strip() for x in v.split(",") if x.strip()]

    @property
    def db_url(self) -> str:
        env = os.getenv("ENVIRONMENT", "local")
        if env == "docker":
            host = "db"
        else:
            host = self.DB_HOST or "localhost"
        return (
            f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{host}:{self.DB_PORT}/{self.DB_NAME}"
        )
