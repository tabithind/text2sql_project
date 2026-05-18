from database.connection import get_connection

class PermissionService:

    PERMISSION_MAP = {
        'lecture'  : ['select'],
        'ecriture' : ['select', 'insert', 'update', 'delete'],
        'admin'    : ['select', 'insert', 'update', 'delete', 'schema']
    }

    @staticmethod
    def get_permissions_utilisateur(utilisateur_id: int, base_id: int) -> list:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT type_acces FROM permissions
                    WHERE utilisateur_id = %s AND base_de_donnees_id = %s
                    AND base_de_donnees_id IN (
                        SELECT id FROM bases_de_donnees WHERE actif = 1
                    )
                """, (utilisateur_id, base_id))
                row = cur.fetchone()
                if not row:
                    return []
                return PermissionService.PERMISSION_MAP.get(row['type_acces'], [])
        finally:
            conn.close()

    @staticmethod
    def peut_faire(utilisateur_id: int, base_id: int, operation: str) -> bool:
        perms = PermissionService.get_permissions_utilisateur(utilisateur_id, base_id)
        return operation.lower() in perms

    @staticmethod
    def verifier_ou_refuser(utilisateur_id: int, base_id: int, operation: str) -> dict:
        if PermissionService.peut_faire(utilisateur_id, base_id, operation):
            return {'ok': True}
        return {
            'ok'     : False,
            'erreur' : f"Permission refusée — opération '{operation}' non autorisée pour votre compte.",
            'code'   : 'PERMISSION_DENIED'
        }

    @staticmethod
    def get_bases_accessibles(utilisateur_id: int) -> list:
        """Retourne la liste des bases de données auxquelles l'utilisateur a accès."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT b.id, b.nom, b.type, p.type_acces 
                    FROM bases_de_donnees b
                    JOIN permissions p ON b.id = p.base_de_donnees_id
                    WHERE p.utilisateur_id = %s AND b.actif = 1
                """, (utilisateur_id,))
                return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def attribuer_permission(utilisateur_id: int, base_id: int, type_acces: str) -> dict:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO permissions (utilisateur_id, base_de_donnees_id, type_acces) 
                       VALUES (%s, %s, %s)
                       ON DUPLICATE KEY UPDATE type_acces = VALUES(type_acces)""",
                    (utilisateur_id, base_id, type_acces)
                )
                conn.commit()
                return {'ok': True}
        except Exception as e:
            conn.rollback()
            return {'ok': False, 'erreur': str(e)}
        finally:
            conn.close()

    @staticmethod
    def revoquer_permission(utilisateur_id: int, base_id: int) -> dict:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM permissions WHERE utilisateur_id = %s AND base_de_donnees_id = %s",
                    (utilisateur_id, base_id)
                )
                conn.commit()
                return {'ok': True}
        except Exception as e:
            conn.rollback()
            return {'ok': False, 'erreur': str(e)}
        finally:
            conn.close()
