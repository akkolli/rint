import psycopg2
from psycopg2 import sql

conn = psycopg2.connect(
    host="postgres", dbname="postgres", user="postgres", password="postgres"
)
conn.autocommit = True

with conn.cursor() as cur:
    cur.execute(
        sql.SQL("""
        CREATE USER fittrackee WITH PASSWORD 'fittrackee';
    """)
    )
    cur.execute(
        sql.SQL("""
        CREATE SCHEMA fittrackee AUTHORIZATION fittrackee;
    """)
    )
    databases = [
        "fittrackee_test",
        *(f"fittrackee_test_gw{i}" for i in range(8)),
    ]
    for database in databases:
        cur.execute(
            sql.SQL("CREATE DATABASE {} OWNER fittrackee").format(
                sql.Identifier(database)
            )
        )
conn.close()

for database in databases:
    conn = psycopg2.connect(
        host="postgres",
        dbname=database,
        user="postgres",
        password="postgres",
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("""
            CREATE EXTENSION IF NOT EXISTS postgis;
        """)
        )
    conn.close()
