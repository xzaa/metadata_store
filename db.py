import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'graphdb'),
    'user': os.getenv('DB_USER', 'flask_user'),
    'password': os.getenv('DB_PASS', 'flask_pass'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
}


def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO data_arch;")
    return conn


def fetch_all(query, params=None):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            return cur.fetchall()


def execute_many(query, params_list):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(query, params_list)
        conn.commit()


def execute(query, params=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
        conn.commit()
