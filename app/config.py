from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


@dataclass(frozen=True)
class OracleConfig:
    host: str = _env("ORACLE_HOST", "localhost")
    port: int = int(_env("ORACLE_PORT", "1521"))
    service_name: str = _env("ORACLE_SERVICE_NAME", "XE")
    username: str = _env("ORACLE_USERNAME", "ehr_user")
    password: str = _env("ORACLE_PASSWORD", "change_me")
    min_pool: int = int(_env("ORACLE_MIN_POOL", "1"))
    max_pool: int = int(_env("ORACLE_MAX_POOL", "5"))
    increment: int = int(_env("ORACLE_INCREMENT", "1"))

    @property
    def dsn(self) -> str:
        return f"{self.host}:{self.port}/{self.service_name}"


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
    ORACLE = OracleConfig()
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env("FLASK_ENV", "development") == "production"
