"""Thin connection helpers for the two databases.

Postgres  -> OLTP: accounts, campaigns, agent decisions.
ClickHouse-> OLAP: the high-volume event stream + rollups.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import clickhouse_connect
import psycopg
from psycopg.rows import dict_row

from .config import CH, PG


@contextmanager
def pg_conn() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(PG.dsn, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ch_client():
    return clickhouse_connect.get_client(
        host=CH.host,
        port=CH.port,
        username=CH.user,
        password=CH.password,
        database=CH.db,
    )
