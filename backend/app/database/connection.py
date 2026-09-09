from collections.abc import Generator

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

from app.config import get_settings

_pool: MySQLConnectionPool | None = None


def get_pool() -> MySQLConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = MySQLConnectionPool(
            pool_name="nutrition_pool",
            pool_size=8,
            host=settings.mysql_host,
            port=settings.mysql_port,
            user=settings.mysql_user,
            password=settings.mysql_password,
            database=settings.mysql_database,
            autocommit=False,
        )
    return _pool


def get_connection():
    return get_pool().get_connection()


def get_db() -> Generator:
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def ping_database() -> bool:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return True
    finally:
        connection.close()
