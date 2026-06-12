from database.connection import get_connection
from services.crypto_service import CryptoService
from config.constants import URL_TEMPLATES

class DatabaseService:
    @staticmethod
    def tester_connexion(type_db: str, url: str) -> dict:
        """Teste une connexion à une base de données."""
        from services.database_connectors import ConnectorFactory
        try:
            # S'assurer que l'URL est une string UTF-8 valide
            if isinstance(url, bytes):
                try:
                    url = url.decode('utf-8')
                except UnicodeDecodeError:
                    url = url.decode('latin-1')
            elif not isinstance(url, str):
                url = str(url)
            
            connector = ConnectorFactory.get_connector(type_db)
            return connector.test_connection(url)
        except Exception as e:
            error_msg = str(e)
            # Si c'est une erreur d'encoding, essayer de la décoder proprement
            if isinstance(error_msg, bytes):
                try:
                    error_msg = error_msg.decode('utf-8', errors='replace')
                except:
                    error_msg = repr(error_msg)
            return {'ok': False, 'erreur': error_msg}

    @staticmethod
    def build_url(type_db: str, host: str, port: int, database: str, user: str, password: str, **kwargs) -> str:
        """Construit une URL de connexion à partir des champs manuels."""
        from services.database_connectors import ConnectorFactory
        import urllib.parse

        try:
            connector = ConnectorFactory.get_connector(type_db)

            # Convertir les paramètres en strings UTF-8 et gérer les None
            def ensure_utf8_str(value):
                if value is None:
                    return None
                if isinstance(value, bytes):
                    # Si c'est des bytes, essayer de décoder en UTF-8, sinon en latin-1
                    try:
                        return value.decode('utf-8')
                    except UnicodeDecodeError:
                        # Fallback to latin-1 which can decode any byte sequence
                        return value.decode('latin-1').encode('utf-8').decode('utf-8', errors='replace')
                # Si c'est une string, s'assurer qu'elle est en UTF-8
                value_str = str(value) if value else None
                if value_str:
                    try:
                        # Essayer d'encoder en UTF-8 pour valider
                        value_str.encode('utf-8')
                    except UnicodeEncodeError:
                        # Si ça échoue, c'est que la string contient des caractères invalides
                        value_str = value_str.encode('latin-1', errors='replace').decode('utf-8', errors='replace')
                return value_str

            host = ensure_utf8_str(host)
            user = ensure_utf8_str(user)
            password = ensure_utf8_str(password)
            database = ensure_utf8_str(database)
            
            # Valider que les champs requis ne sont pas vides
            # Pour MongoDB, user et password sont optionnels
            # Pour MySQL, password est optionnel
            if type_db == 'mongodb':
                missing = [f for f in ['host', 'database'] if not locals().get(f)]
                if missing:
                    raise ValueError(f"Paramètres manquants pour MongoDB : {', '.join(missing)}")
            elif type_db == 'mysql':
                missing = [f for f in ['host', 'user', 'database'] if not locals().get(f)]
                if missing:
                    raise ValueError(f"Paramètres obligatoires manquants pour MySQL : {', '.join(missing)}")
            else:
                missing = [f for f in ['host', 'user', 'password', 'database'] if not locals().get(f)]
                if missing:
                    raise ValueError(f"Paramètres obligatoires manquants : {', '.join(missing)}")

            # Encoder les paramètres spéciaux (caractères réservés) en UTF-8
            # CRITICAL: Encode each parameter carefully to avoid corruption
            try:
                user_encoded     = urllib.parse.quote(user, safe='') if user else ""
                password_encoded = urllib.parse.quote(password, safe='') if password else ""
                database_encoded = urllib.parse.quote(database, safe='') if database else ""
            except Exception as e:
                raise ValueError(f"Erreur lors du encoding des paramètres: {str(e)}")

            # Construire l'URL de base
            if type_db == 'mongodb':
                # MongoDB: user et password sont optionnels
                if user and password:
                    url = f"mongodb://{user_encoded}:{password_encoded}@{host}:{port}/{database_encoded}"
                elif user:
                    url = f"mongodb://{user_encoded}@{host}:{port}/{database_encoded}"
                else:
                    url = f"mongodb://{host}:{port}/{database_encoded}"

                # Ajouter les paramètres optionnels
                params = []
                if kwargs.get('authSource'):
                    params.append(f"authSource={kwargs.get('authSource')}")
                if kwargs.get('replSet'):
                    params.append(f"replicaSet={kwargs.get('replSet')}")

                if params:
                    url += "?" + "&".join(params)
                return url

            elif type_db == 'sqlserver':
                # SQL Server: port est optionnel, host s'appelle "server"
                server = host
                if port:
                    server = f"{server},{port}"

                url = f"mssql+pyodbc://{user_encoded}:{password_encoded}@{server}/{database_encoded}"

                # Ajouter les paramètres optionnels
                params = []
                if kwargs.get('encrypt'):
                    params.append(f"encrypt={kwargs.get('encrypt')}")
                if kwargs.get('trustServerCertificate'):
                    params.append(f"trustServerCertificate={kwargs.get('trustServerCertificate')}")
                params.append("driver=ODBC+Driver+17+for+SQL+Server")

                if params:
                    url += "?" + "&".join(params)
                return url

            elif type_db == 'postgresql':
                url = f"postgresql+psycopg2://{user_encoded}:{password_encoded}@{host}:{port}/{database_encoded}"

                # Ajouter les paramètres optionnels
                params = []
                if kwargs.get('sslmode'):
                    params.append(f"sslmode={kwargs.get('sslmode')}")

                if params:
                    url += "?" + "&".join(params)
                return url

            else:  # MySQL
                url = f"mysql+pymysql://{user_encoded}:{password_encoded}@{host}:{port}/{database_encoded}"

                # Ajouter les paramètres optionnels
                params = []
                if kwargs.get('charset'):
                    params.append(f"charset={kwargs.get('charset')}")

                if params:
                    url += "?" + "&".join(params)
                return url

        except Exception as e:
            raise ValueError(f"Erreur lors de la construction de l'URL : {str(e)}")

    @staticmethod
    def enregistrer_base_url(admin_id: int, nom: str, type_db: str, url_connexion: str) -> dict:
        """Enregistre une base de données en mode URL."""
        test = DatabaseService.tester_connexion(type_db, url_connexion)
        if not test['ok']:
            return test

        # Extraire le schéma de la base
        schema_json = None
        try:
            from services.database_connectors import ConnectorFactory
            import json
            connector = ConnectorFactory.get_connector(type_db)
            db_conn = connector.connect(url_connexion)
            try:
                schema_dict = connector.extract_schema(db_conn)
                schema_json = json.dumps(schema_dict, ensure_ascii=False)
            finally:
                connector.close(db_conn)
        except Exception as ex:
            import logging
            logging.getLogger(__name__).error(f"Erreur d'extraction automatique du schéma (URL) : {ex}")

        chiffrement = CryptoService.chiffrer(url_connexion)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO bases_de_donnees 
                       (admin_id, nom, type, mode_connexion, url_connexion, url_iv, url_auth_tag, schema_db) 
                       VALUES (%s, %s, %s, 'url', %s, %s, %s, %s)""",
                    (admin_id, nom, type_db, chiffrement['cle_chiffree'], chiffrement['iv'], chiffrement['auth_tag'], schema_json)
                )
                conn.commit()
                return {'ok': True, 'base_id': cur.lastrowid}
        except Exception as e:
            conn.rollback()
            return {'ok': False, 'erreur': str(e)}
        finally:
            conn.close()

    @staticmethod
    def enregistrer_base_manuel(admin_id: int, nom: str, type_db: str, host: str, port: int, nom_base: str, utilisateur_db: str, password_db: str, **kwargs) -> dict:
        """Enregistre une base de données en mode Manuel avec support des champs optionnels."""
        url = DatabaseService.build_url(type_db, host, port, nom_base, utilisateur_db, password_db, **kwargs)
        test = DatabaseService.tester_connexion(type_db, url)
        if not test['ok']:
            return test

        # Extraire le schéma de la base
        schema_json = None
        try:
            from services.database_connectors import ConnectorFactory
            import json
            connector = ConnectorFactory.get_connector(type_db)
            db_conn = connector.connect(url)
            try:
                schema_dict = connector.extract_schema(db_conn)
                schema_json = json.dumps(schema_dict, ensure_ascii=False)
            finally:
                connector.close(db_conn)
        except Exception as ex:
            import logging
            logging.getLogger(__name__).error(f"Erreur d'extraction automatique du schéma (manuel) : {ex}")

        chiffrement = CryptoService.chiffrer(password_db or "")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO bases_de_donnees
                       (admin_id, nom, type, mode_connexion, host, port, nom_base, utilisateur_db, password_db, pw_iv, pw_auth_tag, schema_db)
                       VALUES (%s, %s, %s, 'manuel', %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (admin_id, nom, type_db, host, port, nom_base, utilisateur_db, chiffrement['cle_chiffree'], chiffrement['iv'], chiffrement['auth_tag'], schema_json)
                )
                conn.commit()
                return {'ok': True, 'base_id': cur.lastrowid}
        except Exception as e:
            conn.rollback()
            return {'ok': False, 'erreur': str(e)}
        finally:
            conn.close()

    @staticmethod
    def get_bases_par_admin(admin_id: int) -> list:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, nom, type, mode_connexion, actif, created_at FROM bases_de_donnees WHERE admin_id = %s", 
                    (admin_id,)
                )
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_url_connexion(base_id: int) -> str:
        """Récupère l'URL de connexion complète et déchiffrée."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM bases_de_donnees WHERE id = %s", (base_id,))
                base = cur.fetchone()
                if not base:
                    raise ValueError("Base de données introuvable.")

                if base['mode_connexion'] == 'url':
                    return CryptoService.dechiffrer(base['url_connexion'], base['url_iv'], base['url_auth_tag'])
                else:
                    password = CryptoService.dechiffrer(base['password_db'], base['pw_iv'], base['pw_auth_tag'])
                    return DatabaseService.build_url(
                        base['type'], base['host'], base['port'], base['nom_base'], base['utilisateur_db'], password
                    )
        finally:
            conn.close()

    @staticmethod
    def supprimer_base(base_id: int) -> dict:
        """Supprime une base de données enregistrée."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Vérifier que la base existe
                cur.execute("SELECT id FROM bases_de_donnees WHERE id = %s", (base_id,))
                if not cur.fetchone():
                    return {'ok': False, 'erreur': 'Base de données introuvable.'}

                # Supprimer les permissions associées
                cur.execute("DELETE FROM permissions WHERE base_de_donnees_id = %s", (base_id,))

                # Supprimer la base
                cur.execute("DELETE FROM bases_de_donnees WHERE id = %s", (base_id,))

                conn.commit()
                return {'ok': True}
        except Exception as e:
            conn.rollback()
            return {'ok': False, 'erreur': str(e)}
        finally:
            conn.close()
