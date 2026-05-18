from services.user_service import UserService
from services.database_service import DatabaseService
from services.permission_service import PermissionService

class AdminController:
    def __init__(self, admin_data: dict):
        self.admin = admin_data
        self.admin_id = self.admin.get('id')

    # Users
    def get_users(self) -> list:
        return UserService.get_utilisateurs_par_admin(self.admin_id)

    def add_user(self, prenom: str, nom: str, email: str, password: str) -> dict:
        if not all([prenom, nom, email, password]):
            return {'ok': False, 'erreur': "Tous les champs sont obligatoires."}
        return UserService.creer_utilisateur(self.admin_id, prenom, nom, email, password)

    def edit_user(self, user_id: int, prenom: str, nom: str, email: str, password: str = None) -> dict:
        if not all([prenom, nom, email]):
            return {'ok': False, 'erreur': "Prénom, nom et email sont obligatoires."}
        return UserService.modifier_utilisateur(user_id, prenom, nom, email, password)

    def delete_user(self, user_id: int) -> dict:
        return UserService.supprimer_utilisateur(user_id)

    # Databases
    def get_databases(self) -> list:
        return DatabaseService.get_bases_par_admin(self.admin_id)

    def test_connection(self, type_db: str, mode: str, data: dict) -> dict:
        if mode == 'url':
            return DatabaseService.tester_connexion(type_db, data.get('url'))
        else:
            # Extraire les champs optionnels
            optional_fields = {}
            for key in ['charset', 'sslmode', 'authSource', 'replSet', 'encrypt', 'trustServerCertificate']:
                if data.get(key):
                    optional_fields[key] = data.get(key)

            url = DatabaseService.build_url(
                type_db, data.get('host'), data.get('port'),
                data.get('database'), data.get('user'), data.get('password'),
                **optional_fields
            )
            return DatabaseService.tester_connexion(type_db, url)

    def save_database(self, nom: str, type_db: str, mode: str, data: dict) -> dict:
        if mode == 'url':
            return DatabaseService.enregistrer_base_url(self.admin_id, nom, type_db, data.get('url'))
        else:
            # Extraire les champs optionnels
            optional_fields = {}
            for key in ['charset', 'sslmode', 'authSource', 'replSet', 'encrypt', 'trustServerCertificate']:
                if data.get(key):
                    optional_fields[key] = data.get(key)

            return DatabaseService.enregistrer_base_manuel(
                self.admin_id, nom, type_db, data.get('host'), data.get('port'),
                data.get('database'), data.get('user'), data.get('password'),
                **optional_fields
            )

    def delete_database(self, base_id: int) -> dict:
        return DatabaseService.supprimer_base(base_id)

    # Permissions
    def update_permission(self, utilisateur_id: int, base_id: int, type_acces: str) -> dict:
        if not type_acces:
            return PermissionService.revoquer_permission(utilisateur_id, base_id)
        else:
            return PermissionService.attribuer_permission(utilisateur_id, base_id, type_acces)
            
    def get_user_permissions(self, utilisateur_id: int, base_id: int) -> list:
        return PermissionService.get_permissions_utilisateur(utilisateur_id, base_id)
