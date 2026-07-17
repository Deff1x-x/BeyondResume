from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg://ebh:ebh@postgres:5432/ebh"
    jwt_secret: str = ""
    jwt_access_ttl_minutes: int = 15
    upload_dir: str = "/app/data/uploads"


settings = Settings()
