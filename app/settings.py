from typing import Sequence

from dotenv import load_dotenv
from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    HOST: str = Field(alias="POSTGRES_HOST", default="localhost")
    PORT: int = Field(alias="POSTGRES_PORT", default=5432)
    NAME: str = Field(alias="POSTGRES_DB", default="auth")
    USER: str = Field(alias="POSTGRES_USER", default="postgres")
    PASSWORD: SecretStr = Field(alias="POSTGRES_PASSWORD", default="postgres")
    LOG_DATABASE: bool = False

    @computed_field
    def async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.USER}:{self.PASSWORD.get_secret_value()}"
            f"@{self.HOST}:{self.PORT}/{self.NAME}"
        )


class RedisSettings(BaseSettings):
    HOST: str = Field(alias="REDIS_HOST", default="localhost")
    PORT: int = Field(alias="REDIS_PORT", default=6379)
    PASSWORD: str = Field(alias="REDIS_PASSWORD", default="")
    DB: int = Field(alias="REDIS_DB", default=0)

    @computed_field
    def url(self) -> str:
        if self.PASSWORD:
            return f"redis://:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"
        return f"redis://{self.HOST}:{self.PORT}/{self.DB}"


class JWTSettings(BaseSettings):
    ACCESS_SECRET: SecretStr = Field(alias="JWT_ACCESS_SECRET", default="change-me-in-production")
    ACCESS_TTL_SECONDS: int = Field(alias="JWT_ACCESS_TTL_SECONDS", default=900)
    REFRESH_TTL_SECONDS: int = Field(alias="JWT_REFRESH_TTL_SECONDS", default=2592000)
    EMAIL_CODE_TTL_SECONDS: int = Field(alias="EMAIL_CODE_TTL_SECONDS", default=900)


class ServiceSettings(BaseSettings):
    CORS_ALLOWED_ORIGINS_STR: str = Field(
        alias="CORS_ALLOWED_ORIGINS",
        default="http://localhost:3000",
    )

    @computed_field
    def CORS_ALLOWED_ORIGINS(self) -> Sequence[str]:
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS_STR.split(",") if o.strip()]


class Settings(BaseSettings):
    DATABASE: DatabaseSettings = Field(default_factory=DatabaseSettings)
    REDIS: RedisSettings = Field(default_factory=RedisSettings)
    JWT: JWTSettings = Field(default_factory=JWTSettings)
    SERVICE: ServiceSettings = Field(default_factory=ServiceSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


load_dotenv()
settings = Settings()
