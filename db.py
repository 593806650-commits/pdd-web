import sqlite3
from flask import g

DB_PATH = "saas.db"

def get_conn():
    if "conn" not in g:
        g.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return g.conn

def close_conn(exception):
    conn = g.pop("conn", None)
    if conn is not None:
        conn.close()