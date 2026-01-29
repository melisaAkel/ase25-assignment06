# db.py
import os
import sqlite3
from flask import current_app, g

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_db_path(app) -> str:
    os.makedirs(app.instance_path, exist_ok=True)
    return os.path.join(app.instance_path, "app.sqlite")


def get_db(app):
    if "db" not in g:
        path = get_db_path(app)
        db = sqlite3.connect(path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON;")
        g.db = db
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    path = get_db_path(app)
    os.makedirs(app.instance_path, exist_ok=True)

    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        db.executescript(f.read())

    db.commit()
    db.close()
