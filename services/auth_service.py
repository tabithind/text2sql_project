import bcrypt
from database.connection import get_connection

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash un mot de passe avec bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Vérifie un mot de passe haché avec bcrypt."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except ValueError:
            return False

    @staticmethod
    def login_admin(email: str, password: str) -> dict:
        """
        Tente de connecter un admin.
        Retourne un dictionnaire avec le succès et les infos de l'admin.
        """
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM admins WHERE email = %s AND actif = 1", (email,))
                admin = cur.fetchone()
                
                if admin and AuthService.verify_password(password, admin['password_hash']):
                    # Ne jamais retourner le hash
                    del admin['password_hash']
                    return {'ok': True, 'admin': admin}
                
                return {'ok': False, 'erreur': 'Email ou mot de passe incorrect.'}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}
        finally:
            conn.close()

    @staticmethod
    def register_admin(prenom: str, nom: str, email: str, password: str, entreprise: str) -> dict:
        """
        Inscrit un nouvel administrateur.
        """
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Vérifier si l'email existe déjà
                cur.execute("SELECT id FROM admins WHERE email = %s", (email,))
                if cur.fetchone():
                    return {'ok': False, 'erreur': 'Cet email est déjà utilisé.'}
                
                hashed_pw = AuthService.hash_password(password)
                cur.execute(
                    "INSERT INTO admins (prenom, nom, email, password_hash, entreprise) VALUES (%s, %s, %s, %s, %s)",
                    (prenom, nom, email, hashed_pw, entreprise)
                )
                conn.commit()
                admin_id = cur.lastrowid
                return {'ok': True, 'admin_id': admin_id}
        except Exception as e:
            conn.rollback()
            return {'ok': False, 'erreur': str(e)}
        finally:
            conn.close()

    @staticmethod
    def login_utilisateur(email: str, password: str) -> dict:
        """
        Tente de connecter un utilisateur.
        Retourne un dictionnaire avec le succès et les infos de l'utilisateur.
        """
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM utilisateurs WHERE email = %s AND actif = 1", (email,))
                user = cur.fetchone()
                
                if user and AuthService.verify_password(password, user['password_hash']):
                    del user['password_hash']
                    return {'ok': True, 'utilisateur': user}
                
                return {'ok': False, 'erreur': 'Email ou mot de passe incorrect.'}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}
        finally:
            conn.close()
