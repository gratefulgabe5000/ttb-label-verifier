from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/workingfiles.db"
    upload_dir: str = "./data/uploads"

    jwt_secret: str = "change-me-to-a-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    cors_origins: str = "http://localhost:5173"

    # Optional override for pytesseract's tesseract binary path (Windows dev
    # machines where Tesseract isn't on PATH). Unset on Linux/Railway, where
    # the Tesseract apt package is on PATH (WBS.md Note 7, contingency #1).
    tesseract_cmd: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
