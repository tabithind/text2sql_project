import sys
import os
from dotenv import load_dotenv

# Resolve the directory of the executable or script
if hasattr(sys, '_MEIPASS'):
    # Running as a bundled executable; .env should be next to the .exe
    base_dir = os.path.dirname(sys.executable)
else:
    # Running in development mode
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

dotenv_path = os.path.join(base_dir, '.env')
load_dotenv(dotenv_path)

class Settings:
    # Central Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'queryai_db')

    # Security
    MASTER_ENCRYPTION_KEY = os.environ.get('MASTER_ENCRYPTION_KEY')
    if MASTER_ENCRYPTION_KEY:
        try:
            MASTER_ENCRYPTION_KEY_BYTES = bytes.fromhex(MASTER_ENCRYPTION_KEY)
        except ValueError:
            MASTER_ENCRYPTION_KEY_BYTES = None
    else:
        MASTER_ENCRYPTION_KEY_BYTES = None

    # Application Defaults
    DEFAULT_IA_SERVICE = os.environ.get('DEFAULT_IA_SERVICE', 'claude')

settings = Settings()
