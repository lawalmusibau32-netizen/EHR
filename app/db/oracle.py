from __future__ import annotations

from contextlib import contextmanager

import oracledb


def create_pool(oracle_config):
    return oracledb.create_pool(
        user=oracle_config.username,
        password=oracle_config.password,
        dsn=oracle_config.dsn,
        min=oracle_config.min_pool,
        max=oracle_config.max_pool,
        increment=oracle_config.increment,
        getmode=oracledb.POOL_GETMODE_WAIT,
    )


@contextmanager
def get_connection(pool):
    connection = pool.acquire()
    try:
        yield connection
    finally:
        connection.close()


def health_check(pool) -> bool:
    with get_connection(pool) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
    return True

