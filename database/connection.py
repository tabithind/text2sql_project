import pymysql
import pymysql.cursors
from config.settings import settings

CENTRAL_DB_CONFIG = {
    'host'        : settings.MYSQL_HOST,
    'port'        : settings.MYSQL_PORT,
    'user'        : settings.MYSQL_USER,
    'password'    : settings.MYSQL_PASSWORD,
    'database'    : settings.MYSQL_DATABASE,
    'charset'     : 'utf8mb4',
    'cursorclass' : pymysql.cursors.DictCursor,
    'autocommit'  : True,
    'read_timeout': 30,
    'write_timeout': 30
}

def get_connection():
    """Retourne une connexion à queryai_db (MySQL via XAMPP)."""
    return pymysql.connect(**CENTRAL_DB_CONFIG)
