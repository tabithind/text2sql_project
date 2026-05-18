from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from services.permission_service import PermissionService
from services.ia_service import IAService

class BaseMCP(ABC):

    # Connexion
    @abstractmethod
    def connect(self, url: str) -> Dict[str, Any]:
        """Connecte à la base et retourne un connection_id."""
        pass

    @abstractmethod
    def disconnect(self, connection_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_databases(self, connection_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_connections(self) -> Dict[str, Any]:
        pass

    # Schéma
    @abstractmethod
    def list_tables(self, connection_id: str) -> Dict[str, Any]:
        """Liste toutes les tables / collections."""
        pass

    def get_schema_snapshot(self, connection_id: str, utilisateur_id: int, base_id: int, refresh: bool = False) -> Dict[str, Any]:
        """
        Retourne le schéma complet.
        Vérifie la permission 'schema' avant d'exécuter.
        """
        perm_check = PermissionService.verifier_ou_refuser(utilisateur_id, base_id, 'schema')
        if not perm_check['ok']:
            return perm_check
        return self._get_schema_snapshot_impl(connection_id, refresh)

    @abstractmethod
    def _get_schema_snapshot_impl(self, connection_id: str, refresh: bool = False) -> Dict[str, Any]:
        pass

    # Génération de requête
    def generate_read_query(self, connection_id: str, user_query: str, utilisateur_id: int, base_id: int, nom_service: str) -> Dict[str, Any]:
        """Génère une requête de lecture depuis le langage naturel."""
        perm_check = PermissionService.verifier_ou_refuser(utilisateur_id, base_id, 'select')
        if not perm_check['ok']:
            return perm_check
        
        schema_data = self.get_schema_snapshot(connection_id, utilisateur_id, base_id)
        schema_str = str(schema_data.get('schema', '')) if schema_data.get('ok') else ""
        
        try:
            query = IAService.generate_query(
                utilisateur_id=utilisateur_id, 
                nom_service=nom_service, 
                user_query=user_query, 
                schema=schema_str, 
                is_mongodb=self.is_mongodb(), 
                base_id=base_id
            )
            return {'ok': True, 'query': query}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def generate_write_query(self, connection_id: str, user_query: str, utilisateur_id: int, base_id: int, nom_service: str) -> Dict[str, Any]:
        """Génère une requête d'écriture depuis le langage naturel."""
        intention = IAService.detecter_intention(user_query)
        if intention not in ['insert', 'update', 'delete']:
            return {'ok': False, 'erreur': f"Intention d'écriture non détectée. Détectée: {intention}"}
            
        perm_check = PermissionService.verifier_ou_refuser(utilisateur_id, base_id, intention)
        if not perm_check['ok']:
            return perm_check
            
        schema_data = self.get_schema_snapshot(connection_id, utilisateur_id, base_id)
        schema_str = str(schema_data.get('schema', '')) if schema_data.get('ok') else ""
        
        try:
            query = IAService.generate_query(
                utilisateur_id=utilisateur_id, 
                nom_service=nom_service, 
                user_query=user_query, 
                schema=schema_str, 
                is_mongodb=self.is_mongodb(), 
                base_id=base_id
            )
            return {'ok': True, 'query': query, 'intention': intention}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    # Exécution
    @abstractmethod
    def execute_read_query(self, connection_id: str, query: Any, max_rows: int = 500, utilisateur_id: int = 0, base_id: int = 0) -> Dict[str, Any]:
        """Exécute une requête de lecture, retourne colonnes + lignes."""
        pass

    @abstractmethod
    def preview_write_impact(self, connection_id: str, query: Any) -> Dict[str, Any]:
        """Estime le nombre de lignes affectées SANS exécuter."""
        pass

    @abstractmethod
    def execute_write_query(self, connection_id: str, query: Any, utilisateur_id: int, base_id: int, confirmed: bool = False) -> Dict[str, Any]:
        """
        Exécute une écriture dans une transaction.
        confirmed=True obligatoire pour exécuter.
        Rollback automatique en cas d'erreur.
        """
        pass

    # One-stop
    def answer(self, connection_id: str, user_query: str, utilisateur_id: int, base_id: int, nom_service: str, want_chart: bool = False) -> Dict[str, Any]:
        """
        Outil principal — gère tout le flux.
        """
        intention = IAService.detecter_intention(user_query)
        
        if intention in ['insert', 'update', 'delete']:
            gen = self.generate_write_query(connection_id, user_query, utilisateur_id, base_id, nom_service)
            if not gen['ok']: return gen
            
            preview = self.preview_write_impact(connection_id, gen['query'])
            return {
                'ok': True, 
                'intention': intention, 
                'query': gen['query'], 
                'preview': preview,
                'requires_confirmation': True
            }
        elif intention == 'schema':
            return self.get_schema_snapshot(connection_id, utilisateur_id, base_id)
        else:
            gen = self.generate_read_query(connection_id, user_query, utilisateur_id, base_id, nom_service)
            if not gen['ok']: return gen
            
            res = self.execute_read_query(connection_id, gen['query'], utilisateur_id=utilisateur_id, base_id=base_id)
            if not res['ok']: return res
            
            # Générer des insights en arrière-plan à partir des résultats
            insights = IAService.generate_insights(
                utilisateur_id=utilisateur_id,
                nom_service=nom_service,
                user_query=user_query,
                query=gen['query'],
                result_data=res
            )
            
            # TODO: Handle want_chart
            return {
                'ok': True,
                'intention': 'select',
                'query': gen['query'],
                'result': res,
                'insights': insights
            }

    # Visualisation
    @abstractmethod
    def render_chart(self, connection_id: str, chart_type: str, x: str, y: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        """Génère un graphique depuis le dernier résultat."""
        pass

    # Historique
    @abstractmethod
    def get_write_history(self, connection_id: str) -> Dict[str, Any]:
        """Retourne l'historique des écritures de la session."""
        pass

    @abstractmethod
    def is_mongodb(self) -> bool:
        """Indicates if the MCP is for MongoDB."""
        pass
