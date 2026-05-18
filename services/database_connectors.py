from abc import ABC, abstractmethod
import urllib.parse
import logging
from config.constants import URL_TEMPLATES

logger = logging.getLogger(__name__)

def ensure_valid_utf8(value):
    """Convertit n'importe quelle valeur en UTF-8 valide sans corruption."""
    if value is None:
        return None
    
    if isinstance(value, bytes):
        try:
            # Essayer UTF-8 d'abord
            return value.decode('utf-8')
        except UnicodeDecodeError:
            # Si échoue, essayer latin-1 (qui peut décoder n'importe quel byte)
            # puis ré-encoder en UTF-8
            return value.decode('latin-1').encode('utf-8').decode('utf-8')
    
    # Si c'est une string, vérifier qu'elle est valide UTF-8
    if isinstance(value, str):
        try:
            # Vérifier qu'on peut l'encoder/décoder
            value.encode('utf-8').decode('utf-8')
            return value
        except UnicodeEncodeError:
            # Si la string contient des caractères non-UTF-8, les remplacer
            return value.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    
    # Sinon, convertir en string
    return str(value)

class BaseDatabaseConnector(ABC):
    @abstractmethod
    def connect(self, url: str):
        """Établit la connexion à la base de données."""
        pass

    @abstractmethod
    def test_connection(self, url: str) -> dict:
        """Teste la connexion et retourne un dictionnaire { 'ok': bool, 'erreur': str }."""
        pass

    @abstractmethod
    def close(self, connection):
        """Ferme la connexion donnée."""
        pass

    @abstractmethod
    def extract_schema(self, connection) -> dict:
        """Extrait le schéma de la base de données sous forme de dictionnaire."""
        pass

    def build_url(self, type_db: str, host: str, port: int, database: str, user: str, password: str) -> str:
        """Construit une URL de connexion à partir des champs manuels."""
        template = URL_TEMPLATES.get(type_db)
        if not template:
            raise ValueError(f"Type de base non supporté : {type_db}")
        return template.format(user=user, password=password, host=host, port=port, database=database)

    def parse_url(self, url: str) -> dict:
        """Parse une URL de connexion pour extraire les composants."""
        # Pour pymysql et pyodbc, sqlalchemy prefixes are often included (mysql+pymysql://, mssql+pyodbc://)
        # We strip them to standard schemes so urllib.parse works smoothly.
        
        # Ensure url is a proper UTF-8 string
        url = ensure_valid_utf8(url)
        
        logger.debug(f"Parsing URL: {url[:100]}...")
        
        if url.startswith('mysql+pymysql://'):
            url = url.replace('mysql+pymysql://', 'mysql://')
        elif url.startswith('postgresql+psycopg2://'):
            url = url.replace('postgresql+psycopg2://', 'postgresql://')
        elif url.startswith('mssql+pyodbc://'):
            url = url.replace('mssql+pyodbc://', 'mssql://')

        try:
            parsed = urllib.parse.urlparse(url)
            
            # Decode URL-encoded components properly with error handling
            username = parsed.username
            password = parsed.password
            hostname = parsed.hostname
            path = parsed.path.lstrip('/') if parsed.path else None
            
            # Log les valeurs brutes
            logger.debug(f"Raw parsed - user: {username}, host: {hostname}, path: {path}")
            
            # Safely unquote with UTF-8 encoding and error handling
            if username:
                try:
                    # Use latin-1 first: it can decode ANY byte value (0x00-0xFF),
                    # then ensure_valid_utf8 normalizes to proper Unicode.
                    username = urllib.parse.unquote(username, encoding='latin-1')
                except Exception:
                    username = urllib.parse.unquote(username, encoding='utf-8', errors='replace')
                username = ensure_valid_utf8(username)
                    
            if password:
                try:
                    # CRITICAL: Use latin-1 to safely decode any percent-encoded byte.
                    # This handles both %E9 (Latin-1 'é') and %C3%A9 (UTF-8 'é').
                    logger.debug(f"Raw password length: {len(password)}")
                    password = urllib.parse.unquote(password, encoding='latin-1')
                except Exception as e:
                    logger.error(f"Error unquoting password: {e}")
                    password = urllib.parse.unquote(password, encoding='utf-8', errors='replace')
                password = ensure_valid_utf8(password)
                    
            if path:
                try:
                    path = urllib.parse.unquote(path, encoding='latin-1')
                except Exception:
                    path = urllib.parse.unquote(path, encoding='utf-8', errors='replace')
                path = ensure_valid_utf8(path)
            
            result = {
                'host': hostname,
                'port': parsed.port,
                'user': username,
                'password': password,
                'database': path
            }
            
            logger.debug(f"Parsed URL successfully - host: {hostname}, port: {parsed.port}, user: {username}, db: {path}")
            
            return result
        except Exception as e:
            logger.error(f"Error parsing URL: {e}")
            raise ValueError(f"Erreur lors du parsing de l'URL de connexion: {str(e)}")


class MySQLConnector(BaseDatabaseConnector):
    def connect(self, url: str):
        import pymysql
        
        # Ensure URL is a proper UTF-8 string
        url = ensure_valid_utf8(url)
        
        # Always parse URL and pass parameters explicitly
        params = self.parse_url(url)
        
        # Ensure all parameters are valid UTF-8
        host = ensure_valid_utf8(params['host'])
        port = params['port'] or 3306
        user = ensure_valid_utf8(params['user'])
        password = ensure_valid_utf8(params['password'])
        database = ensure_valid_utf8(params['database'])
        
        logger.debug(f"MySQL connect: host={host}, port={port}, user={user}, db={database}")
        
        return pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            connect_timeout=5,
            cursorclass=pymysql.cursors.DictCursor
        )

    def test_connection(self, url: str) -> dict:
        try:
            conn = self.connect(url)
            conn.ping()
            self.close(conn)
            return {'ok': True}
        except Exception as e:
            error_msg = ensure_valid_utf8(str(e))
            logger.error(f"MySQL test_connection failed: {error_msg}")
            return {'ok': False, 'erreur': error_msg}

    def close(self, connection):
        if connection:
            try:
                connection.close()
            except Exception:
                pass

    def extract_schema(self, connection) -> dict:
        schema = {}
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [list(row.values())[0] for row in cursor.fetchall()]
            
            for table_name in tables:
                cursor.execute(f"DESCRIBE `{table_name}`")
                cols = cursor.fetchall()
                schema[table_name] = [
                    {
                        "Field": c.get('Field'), 
                        "Type": c.get('Type'), 
                        "Null": c.get('Null'), 
                        "Key": c.get('Key'), 
                        "Default": str(c.get('Default')) if c.get('Default') is not None else None, 
                        "Extra": c.get('Extra')
                    }
                    for c in cols
                ]
        return schema


class PostgreSQLConnector(BaseDatabaseConnector):
    def connect(self, url: str):
        import psycopg2
        import psycopg2.extras
        
        # Ensure URL is a proper UTF-8 string
        url = ensure_valid_utf8(url)
        
        # Always parse URL and pass parameters explicitly to avoid encoding issues
        params = self.parse_url(url)
        
        # S'assurer que chaque paramètre est valide UTF-8
        host = ensure_valid_utf8(params['host'])
        port = params['port'] or 5432
        user = ensure_valid_utf8(params['user'])
        password = ensure_valid_utf8(params['password'])
        database = ensure_valid_utf8(params['database'])
        
        logger.debug(f"PostgreSQL connect: host={host}, port={port}, user={user}, db={database}")
        
        # Valider et corriger les paramètres
        for name, value in [('host', host), ('user', user), ('password', password), ('database', database)]:
            if not value:
                raise ValueError(f"Le paramètre '{name}' ne peut pas être vide")

        # Forcer chaque paramètre en str Python pur (pas de bytes)
        def force_str(v):
            if isinstance(v, bytes):
                try:
                    return v.decode('utf-8')
                except UnicodeDecodeError:
                    return v.decode('latin-1')
            return str(v) if v is not None else v

        host     = force_str(host)
        user     = force_str(user)
        password = force_str(password)
        database = force_str(database)

        logger.info(f"Connecting to PostgreSQL: {host}:{port}/{database}")

        def _try_connect(**extra):
            return psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                connect_timeout=5,
                client_encoding='utf8',
                **extra
            )

        try:
            return _try_connect()
        except Exception as e:
            error_str = str(e)
            logger.error(f"PostgreSQL connection failed: {error_str}")

            # Essai sans SSL
            if 'ssl' in error_str.lower() or 'certificate' in error_str.lower():
                try:
                    logger.info("Retrying without SSL...")
                    return _try_connect(sslmode='disable')
                except Exception as e2:
                    raise Exception(f"PostgreSQL Connection Error (SSL disabled): {str(e2)}")

            # Autres erreurs
            raise Exception(f"PostgreSQL Connection Error: {error_str}")

    def test_connection(self, url: str) -> dict:
        try:
            conn = self.connect(url)
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            self.close(conn)
            return {'ok': True}
        except Exception as e:
            error_msg = ensure_valid_utf8(str(e))
            logger.error(f"PostgreSQL test_connection failed: {error_msg}")
            return {'ok': False, 'erreur': error_msg}

    def close(self, connection):
        if connection:
            try:
                connection.close()
            except Exception:
                pass

    def extract_schema(self, connection) -> dict:
        schema = {}
        with connection.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            tables = [row[0] for row in cursor.fetchall()]
            for table_name in tables:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                """, (table_name,))
                cols = cursor.fetchall()
                schema[table_name] = [
                    {
                        "Field": c[0], 
                        "Type": c[1], 
                        "Null": c[2], 
                        "Default": str(c[3]) if c[3] is not None else None
                    }
                    for c in cols
                ]
        return schema


class SQLServerConnector(BaseDatabaseConnector):
    def _get_best_driver(self):
        import pyodbc
        drivers = pyodbc.drivers()
        # Prefer ODBC Driver 18, 17, then others
        preferred = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "ODBC Driver 13 for SQL Server"]
        for pref in preferred:
            if pref in drivers:
                return pref
        # Fallback to the first available SQL Server driver if any
        for driver in drivers:
            if "SQL Server" in driver:
                return driver
        raise Exception("Aucun driver ODBC pour SQL Server n'a été trouvé sur le système.")

    def _escape_connection_string_value(self, value: str) -> str:
        """Échappe les caractères spéciaux dans les valeurs de chaîne de connexion pyodbc."""
        if not value:
            return value
        # Ensure value is a string
        if isinstance(value, bytes):
            value = value.decode('utf-8', errors='replace')
        else:
            value = str(value)
        # Pour pyodbc, les accolades doivent être doublées dans les chaînes de connexion
        value = value.replace('}', '}}').replace('{', '{{')
        return value

    def connect(self, url: str):
        import pyodbc
        
        # Ensure URL is a proper UTF-8 string
        if isinstance(url, bytes):
            url = url.decode('utf-8', errors='replace')
        elif not isinstance(url, str):
            url = str(url)
            
        params = self.parse_url(url)
        driver = self._get_best_driver()
        
        server = params['host']
        if params['port']:
            server = f"{server},{params['port']}"
        
        # Échappe les valeurs spéciales dans la chaîne de connexion
        user = self._escape_connection_string_value(params['user'])
        password = self._escape_connection_string_value(params['password'])
        database = self._escape_connection_string_value(params['database'])
        
        # Construction de la chaîne de connexion avec les valeurs échappées
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={password};Connection Timeout=5;"
        
        try:
            return pyodbc.connect(conn_str, timeout=5)
        except Exception as e:
            error_str = str(e)
            # Si la connexion échoue, essayer avec TrustServerCertificate
            if "SSL" in error_str or "certificate" in error_str.lower() or "encrypt" in error_str.lower():
                conn_str += "TrustServerCertificate=yes;"
                try:
                    return pyodbc.connect(conn_str, timeout=5)
                except Exception as e2:
                    raise Exception(f"SQL Server Connection Error: {str(e2)}")
            raise

    def test_connection(self, url: str) -> dict:
        try:
            conn = self.connect(url)
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            self.close(conn)
            return {'ok': True}
        except Exception as e:
            error_msg = str(e)
            # Decode error message properly if it's bytes
            if isinstance(error_msg, bytes):
                try:
                    error_msg = error_msg.decode('utf-8', errors='replace')
                except:
                    error_msg = repr(error_msg)
            return {'ok': False, 'erreur': error_msg}

    def close(self, connection):
        if connection:
            try:
                connection.close()
            except Exception:
                pass

    def extract_schema(self, connection) -> dict:
        schema = {}
        with connection.cursor() as cursor:
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
            tables = [row[0] for row in cursor.fetchall()]
            for table_name in tables:
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = ?
                """, (table_name,))
                cols = cursor.fetchall()
                schema[table_name] = [
                    {
                        "Field": c[0], 
                        "Type": c[1], 
                        "Null": c[2], 
                        "Default": str(c[3]) if c[3] is not None else None
                    }
                    for c in cols
                ]
        return schema


class MongoDBConnector(BaseDatabaseConnector):
    def connect(self, url: str):
        import pymongo
        return pymongo.MongoClient(url, serverSelectionTimeoutMS=5000)

    def test_connection(self, url: str) -> dict:
        try:
            client = self.connect(url)
            client.admin.command('ping')
            self.close(client)
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def close(self, connection):
        if connection:
            try:
                connection.close()
            except Exception:
                pass

    def _extract_mongo_schema_for_doc(self, doc: dict) -> list:
        schema = []
        if not isinstance(doc, dict):
            return schema
            
        for k, v in doc.items():
            field_info = {"Field": k, "Type": type(v).__name__}
            if isinstance(v, dict):
                field_info["SubFields"] = self._extract_mongo_schema_for_doc(v)
            elif isinstance(v, list):
                if len(v) > 0:
                    first_elem = v[0]
                    field_info["ElementType"] = type(first_elem).__name__
                    if isinstance(first_elem, dict):
                        field_info["SubFields"] = self._extract_mongo_schema_for_doc(first_elem)
                else:
                    field_info["ElementType"] = "NoneType"
            schema.append(field_info)
        return schema

    def extract_schema(self, connection) -> dict:
        schema = {}
        try:
            db = connection.get_default_database()
            collections = db.list_collection_names()
            for coll_name in collections:
                sample = db[coll_name].find_one()
                if sample:
                    schema[coll_name] = self._extract_mongo_schema_for_doc(sample)
                else:
                    schema[coll_name] = []
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du schéma MongoDB : {e}")
            # Fallback en listant simplement les collections
            try:
                # Si get_default_database() a échoué car pas spécifié, on liste les bases et collections
                dbs = connection.list_database_names()
                for db_name in dbs:
                    if db_name in ['admin', 'config', 'local']:
                        continue
                    db = connection[db_name]
                    for coll_name in db.list_collection_names():
                        sample = db[coll_name].find_one()
                        full_name = f"{db_name}.{coll_name}"
                        if sample:
                            schema[full_name] = self._extract_mongo_schema_for_doc(sample)
                        else:
                            schema[full_name] = []
            except Exception as e2:
                logger.error(f"Fallback MongoDB schema extraction failed: {e2}")
        return schema


class ConnectorFactory:
    _connectors = {
        'mysql': MySQLConnector(),
        'postgresql': PostgreSQLConnector(),
        'sqlserver': SQLServerConnector(),
        'mongodb': MongoDBConnector()
    }

    @classmethod
    def get_connector(cls, type_db: str) -> BaseDatabaseConnector:
        connector = cls._connectors.get(type_db.lower())
        if not connector:
            raise ValueError(f"SGBD non supporté: {type_db}")
        return connector
