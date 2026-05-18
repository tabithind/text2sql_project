from services.mcp.mcp_router import MCPRouter
from services.database_service import DatabaseService
from services.permission_service import PermissionService
from services.ia_service import IAService

class UserController:
    def __init__(self, user_data: dict):
        self.user = user_data
        self.user_id = self.user.get('id')
        self.active_db_id = None
        self.active_mcp = None
        self.connection_id = None
        self.ia_service_name = "claude" # Default

    def get_accessible_databases(self) -> list:
        return PermissionService.get_bases_accessibles(self.user_id)

    def connect_to_database(self, base_id: int) -> dict:
        try:
            # 1. Get database details
            url = DatabaseService.get_url_connexion(base_id)
            
            # Temporary direct db access to get type (ideally through a service method)
            from database.connection import get_connection
            conn = get_connection()
            type_db = None
            nom = None
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT type, nom FROM bases_de_donnees WHERE id = %s", (base_id,))
                    row = cur.fetchone()
                    if row:
                        type_db = row['type']
                        nom = row['nom']
            finally:
                conn.close()

            if not type_db:
                return {'ok': False, 'erreur': 'Base de données non trouvée.'}

            # 2. Disconnect previous
            self.disconnect()

            # 3. Connect new
            mcp = MCPRouter.get(type_db)
            res = mcp.connect(url)
            
            if res['ok']:
                self.active_db_id = base_id
                self.active_mcp = mcp
                self.connection_id = res['connection_id']
                return {'ok': True, 'nom': nom, 'type': type_db}
            return res
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def disconnect(self):
        if self.active_mcp and self.connection_id:
            self.active_mcp.disconnect(self.connection_id)
            self.active_mcp = None
            self.connection_id = None
            self.active_db_id = None

    def set_ia_service(self, nom_service: str):
        self.ia_service_name = nom_service

    def save_api_key(self, nom_service: str, api_key: str) -> dict:
        """Sauvegarde la clé API de l'utilisateur."""
        return IAService.save_api_key(self.user_id, nom_service, api_key)

    def api_key_exists(self, nom_service: str) -> bool:
        """Vérifie si une clé API existe pour ce service."""
        return IAService.api_key_exists(self.user_id, nom_service)

    def delete_api_key(self, nom_service: str) -> dict:
        """Supprime la clé API de l'utilisateur."""
        return IAService.delete_api_key(self.user_id, nom_service)

    def process_query(self, user_query: str) -> dict:
        if not self.active_mcp or not self.connection_id:
            return {'ok': False, 'erreur': 'Aucune base de données connectée.'}
            
        return self.active_mcp.answer(
            connection_id=self.connection_id,
            user_query=user_query,
            utilisateur_id=self.user_id,
            base_id=self.active_db_id,
            nom_service=self.ia_service_name
        )

    def execute_write_confirmation(self, query: str) -> dict:
        if not self.active_mcp or not self.connection_id:
            return {'ok': False, 'erreur': 'Aucune base de données connectée.'}
            
        return self.active_mcp.execute_write_query(
            connection_id=self.connection_id,
            query=query,
            utilisateur_id=self.user_id,
            base_id=self.active_db_id,
            confirmed=True
        )
