import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager

class DatabasePool:
    def __init__(self):
        self.pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST", "db"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
    
    @contextmanager
    def get_connection(self):
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

db_pool = DatabasePool()
