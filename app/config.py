from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


@dataclass(frozen=True)
class PostgresConfig:
    url: str = _first_env("DATABASE_URL", "POSTGRES_URL", "POSTGRES_PRISMA_URL")
    host: str = _env("POSTGRES_HOST", "localhost")
    port: int = int(_env("POSTGRES_PORT", "5432"))
    database: str = _env("POSTGRES_DB", "ehr")
    username: str = _env("POSTGRES_USER", "ehr_user")
    password: str = _env("POSTGRES_PASSWORD", "change_me")
    min_pool: int = int(_env("POSTGRES_MIN_POOL", "1"))
    max_pool: int = int(_env("POSTGRES_MAX_POOL", "5"))

    @property
    def dsn(self) -> str:
        if self.url:
            return self.url
        return (
            f"host={self.host} port={self.port} dbname={self.database} "
            f"user={self.username} password={self.password}"
        )


class Config:
    SECRET_KEY = _env("SECRET_KEY", "change-this-in-production")
    JWT_SECRET_KEY = _env("JWT_SECRET_KEY", SECRET_KEY)
    EHR_ENCRYPTION_KEY = _env("EHR_ENCRYPTION_KEY", "")
    JWT_ISSUER = _env("JWT_ISSUER", "healthiq-ehr")
    JWT_AUDIENCE = _env("JWT_AUDIENCE", "healthiq-users")
    JWT_ACCESS_TOKEN_MINUTES = int(_env("JWT_ACCESS_TOKEN_MINUTES", "30"))
    ACCOUNT_LOCKOUT_ATTEMPTS = int(_env("ACCOUNT_LOCKOUT_ATTEMPTS", "5"))
    ACCOUNT_LOCKOUT_MINUTES = int(_env("ACCOUNT_LOCKOUT_MINUTES", "15"))
    SESSION_TIMEOUT_MINUTES = int(_env("SESSION_TIMEOUT_MINUTES", JWT_ACCESS_TOKEN_MINUTES))
    AUTH_COOKIE_NAME = _env("AUTH_COOKIE_NAME", "ehr_access_token")
    POSTGRES = PostgresConfig()
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env("FLASK_ENV", "development") == "production"
