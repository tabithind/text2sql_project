from database.connection import get_connection

class SettingsManager:
    @staticmethod
    def get_setting(cle: str, utilisateur_id: int = None, admin_id: int = None, default: str = None) -> str:
        """Récupère la valeur d'une préférence."""
        if not utilisateur_id and not admin_id:
            return default

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                if utilisateur_id:
                    cur.execute("SELECT valeur FROM settings WHERE cle = %s AND utilisateur_id = %s", (cle, utilisateur_id))
                elif admin_id:
                    cur.execute("SELECT valeur FROM settings WHERE cle = %s AND admin_id = %s", (cle, admin_id))
                
                row = cur.fetchone()
                if row:
                    return row['valeur']
                return default
        finally:
            conn.close()

    @staticmethod
    def set_setting(cle: str, valeur: str, utilisateur_id: int = None, admin_id: int = None) -> dict:
        """Définit la valeur d'une préférence."""
        if not utilisateur_id and not admin_id:
            return {'ok': False, 'erreur': 'utilisateur_id ou admin_id requis.'}

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # On vérifie si la clé existe déjà
                if utilisateur_id:
                    cur.execute("SELECT id FROM settings WHERE cle = %s AND utilisateur_id = %s", (cle, utilisateur_id))
                else:
                    cur.execute("SELECT id FROM settings WHERE cle = %s AND admin_id = %s", (cle, admin_id))
                
                row = cur.fetchone()
                
                if row:
                    # Update
                    if utilisateur_id:
                        cur.execute("UPDATE settings SET valeur = %s WHERE cle = %s AND utilisateur_id = %s", (valeur, cle, utilisateur_id))
                    else:
                        cur.execute("UPDATE settings SET valeur = %s WHERE cle = %s AND admin_id = %s", (valeur, cle, admin_id))
                else:
                    # Insert
                    if utilisateur_id:
                        cur.execute("INSERT INTO settings (utilisateur_id, cle, valeur) VALUES (%s, %s, %s)", (utilisateur_id, cle, valeur))
                    else:
                        cur.execute("INSERT INTO settings (admin_id, cle, valeur) VALUES (%s, %s, %s)", (admin_id, cle, valeur))
                
                conn.commit()
                return {'ok': True}
        except Exception as e:
            conn.rollback()
            return {'ok': False, 'erreur': str(e)}
        finally:
            conn.close()
