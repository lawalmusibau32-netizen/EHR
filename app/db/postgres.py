from __future__ import annotations

import os
import re
from contextlib import contextmanager
from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


_PARAM_PATTERN = re.compile(r"(?<!:):([A-Za-z_][A-Za-z0-9_]*)")
_LOB_PATTERN = re.compile(
    r"DBMS_LOB\.SUBSTR\(\s*([A-Za-z0-9_.]+)\s*,\s*4000\s*,\s*1\s*\)",
    re.IGNORECASE,
)
_NVL_PATTERN = re.compile(r"\bNVL\s*\(", re.IGNORECASE)
_NUMTODSINTERVAL_MINUTE_PATTERN = re.compile(
    r"NUMTODSINTERVAL\(\s*%\(([A-Za-z_][A-Za-z0-9_]*)\)s\s*,\s*'MINUTE'\s*\)",
    re.IGNORECASE,
)
_NUMTODSINTERVAL_LITERAL_PATTERN = re.compile(
    r"NUMTODSINTERVAL\(\s*(\d+)\s*,\s*'DAY'\s*\)\s*\+\s*NUMTODSINTERVAL\(\s*(\d+)\s*,\s*'HOUR'\s*\)",
    re.IGNORECASE,
)


def _translate_sql(sql: str) -> str:
    translated = sql
    translated = _PARAM_PATTERN.sub(r"%(\1)s", translated)
    translated = _LOB_PATTERN.sub(r"LEFT(\1::text, 4000)", translated)
    translated = _NVL_PATTERN.sub("COALESCE(", translated)
    translated = re.sub(r"\bSYSTIMESTAMP\b", "NOW()", translated, flags=re.IGNORECASE)
    translated = _NUMTODSINTERVAL_MINUTE_PATTERN.sub(r"(%(\1)s || ' minutes')::interval", translated)
    translated = _NUMTODSINTERVAL_LITERAL_PATTERN.sub(
        lambda match: f"INTERVAL '{match.group(1)} day' + INTERVAL '{match.group(2)} hour'",
        translated,
    )
    translated = translated.replace("WHERE ROWNUM <= %(limit)s", "LIMIT %(limit)s")
    translated = re.sub(r"\bFROM\s+DUAL\b", "", translated, flags=re.IGNORECASE)
    return translated


class _CursorProxy:
    def __init__(self, cursor) -> None:
        self._cursor = cursor

    def execute(self, sql: str, params: dict[str, Any] | None = None):
        return self._cursor.execute(_translate_sql(sql), params or {})

    def executemany(self, sql: str, params_seq):
        return self._cursor.executemany(_translate_sql(sql), params_seq)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def close(self):
        return self._cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def __getattr__(self, name: str):
        return getattr(self._cursor, name)


class _ConnectionProxy:
    def __init__(self, connection) -> None:
        self._connection = connection

    def cursor(self):
        return _CursorProxy(self._connection.cursor(row_factory=dict_row))

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()
        return False

    def __getattr__(self, name: str):
        return getattr(self._connection, name)


def create_pool(postgres_config):
    is_production = os.getenv("VERCEL") == "1" or os.getenv("FLASK_ENV") == "production"
    if is_production and not postgres_config.url:
        raise RuntimeError(
            "PostgreSQL connection is not configured for production. "
            "Set DATABASE_URL, POSTGRES_URL, or POSTGRES_PRISMA_URL in Vercel."
        )
    return ConnectionPool(
        conninfo=postgres_config.dsn,
        min_size=postgres_config.min_pool,
        max_size=postgres_config.max_pool,
        kwargs={"autocommit": False},
    )


@contextmanager
def get_connection(pool):
    with pool.connection() as connection:
        yield _ConnectionProxy(connection)


def health_check(pool) -> bool:
    with get_connection(pool) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    return True
