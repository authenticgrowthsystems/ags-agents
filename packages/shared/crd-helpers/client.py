"""PostgreSQL CRD connection client."""
import os
import logging
import psycopg2
import psycopg2.extras
from typing import Optional

logger = logging.getLogger(__name__)


class CRDError(Exception):
    pass


def get_connection():
    """Get PostgreSQL connection. Uses env vars: CRD_HOST, CRD_PORT, CRD_DATABASE, CRD_USER, CRD_PASSWORD."""
    try:
        return psycopg2.connect(
            host=os.environ.get('CRD_HOST', 'pg_n8n'),
            port=int(os.environ.get('CRD_PORT', '5432')),
            database=os.environ.get('CRD_DATABASE', 'ags_crd'),
            user=os.environ.get('CRD_USER', 'ags_crd_user'),
            password=os.environ['CRD_PASSWORD'],
            cursor_factory=psycopg2.extras.RealDictCursor
        )
    except KeyError:
        raise CRDError("CRD_PASSWORD environment variable not set")
    except psycopg2.Error as e:
        raise CRDError(f"Database connection failed: {e}")


class CRDClient:
    """Context manager for CRD database operations."""

    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def close(self):
        self.cursor.close()
        self.conn.close()
