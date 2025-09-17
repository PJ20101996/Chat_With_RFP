# db/database.py

import pymysql
from config import settings  

# Build MySQL connection config
MYSQL_CONFIG = {
    "host": settings.MYSQL_HOST,
    "user": settings.MYSQL_USER,
    "password": settings.MYSQL_PASSWORD,
    "database": settings.MYSQL_DB,
    "port": int(settings.DATABASE_PORT),
    "cursorclass": pymysql.cursors.DictCursor  # fetch results as dict
}

def get_connection():
    """
    Returns a new PyMySQL connection.
    You must close() it manually after use.
    Example:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
    """
    return pymysql.connect(**MYSQL_CONFIG)
