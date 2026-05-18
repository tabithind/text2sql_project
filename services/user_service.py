from database.connection import get_connection
from services.auth_service import AuthService

class UserService:
    @staticmethod
    def get_utilisateurs_par_admin(admin_id: int) -> list:
        """Récupère la liste des utilisateurs pour un admin donné."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, prenom, nom, email, actif, created_at FROM utilisateurs WHERE admin_id = %s", 
                    (admin_id,)
                )
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def creer_utilisateur(admin_id: int, prenom: str, nom: str, email: str, password: str, actif: bool = True) -> dict:
        """Crée un nouvel utilisateur."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM utilisateurs WHERE email = %s", (email,))
                if cur.fetchone():
                    return {'ok': False, 'erreur': 'Cet email est déjà utilisé par un utilisateur.'}
                
                hashed_pw = AuthService.hash_password(password)
                cur.execute(
                    "INSERT INTO utilisateurs (admin_id, prenom, nom, email, password_hash, actif) VALUES (%s, %s, %s, %s, %s, %s)",
                    (admin_id, prenom, nom, email, hashed_pw, actif)
                )
                conn.commit()
                return {'ok': True, 'utilisateur_id': cur.lastrowid}
        except Exception as e:
            conn.rollback()
            return {'ok': False, 'erreur': str(e)}
        finally:
            conn.close()

    @staticmethod
    def modifier_utilisateur(utilisateur_id: int, prenom: str, nom: str, email: str, password: str = None, actif: bool = True) -> dict:
        """Modifie un utilisateur existant."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Vérifier si l'email existe déjà pour un autre user
                cur.execute("SELECT id FROM utilisateurs WHERE email = %s AND id != %s", (email, utilisateur_id))
                if cur.fetchone():
                    return {'ok': False, 'erreur': 'Cet email est déjà utilisé.'}
                
                if password:
                    hashed_pw = AuthService.hash_password(password)
                    cur.execute(
                        "UPDATE utilisateurs SET prenom = %s, nom = %s, email = %s, password_hash = %s, actif = %s WHERE id = %s",
                        (prenom, nom, email, hashed_pw, actif, utilisateur_id)
                    )
                else:
                    cur.execute(
                        "UPDATE utilisateurs SET prenom = %s, nom = %s, email = %s, actif = %s WHERE id = %s",
                        (prenom, nom, email, actif, utilisateur_id)
                    )
                conn.commit()
                return {'ok': True}
        except Exception as e:
            conn.rollback()
            return {'ok': False, 'erreur': str(e)}
        finally:
            conn.close()

    @staticmethod
    def supprimer_utilisateur(utilisateur_id: int) -> dict:
        """Supprime un utilisateur (cascade sur permissions, etc.)."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM utilisateurs WHERE id = %s", (utilisateur_id,))
                conn.commit()
                return {'ok': True}
        except Exception as e:
            conn.rollback()
            return {'ok': False, 'erreur': str(e)}
        finally:
            conn.close()
