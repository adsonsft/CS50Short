import sqlite3
from flask import g

DATABASE = 'short.db'

def get_db():
    """Init database connection"""

    # Check if already exists one connection
    db = getattr(g, '_database', None)

    # If database doesn't have one conextion
    # Open it
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    # Every line is a dictionary
    db.row_factory = sqlite3.Row
    return db

