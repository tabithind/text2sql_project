from typing import Any, Dict, Optional
import json
from bson import ObjectId
from services.mcp.base_mcp import BaseMCP

from services.database_connectors import ConnectorFactory

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

class MongoDBMCP(BaseMCP):
    def __init__(self):
        self._clients: Dict[str, Any] = {}
        self.connector = ConnectorFactory.get_connector('mongodb')

    def _get_db(self, client) -> Any:
        try:
            return client.get_default_database()
        except Exception:
            try:
                dbs = client.list_database_names()
                for db_name in dbs:
                    if db_name not in ['admin', 'config', 'local']:
                        return client[db_name]
            except Exception:
                pass
            return client['test']

    def connect(self, url: str) -> Dict[str, Any]:
        try:
            client = self.connector.connect(url)
            
            import hashlib
            conn_id = hashlib.md5(url.encode()).hexdigest()
            self._clients[conn_id] = client
            return {'ok': True, 'connection_id': conn_id}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def disconnect(self, connection_id: str) -> Dict[str, Any]:
        if connection_id in self._clients:
            self.connector.close(self._clients[connection_id])
            del self._clients[connection_id]
        return {'ok': True}

    def list_databases(self, connection_id: str) -> Dict[str, Any]:
        if connection_id not in self._clients: return {'ok': False, 'erreur': 'Non connecté'}
        try:
            client = self._clients[connection_id]
            dbs = client.list_database_names()
            return {'ok': True, 'databases': dbs}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def list_connections(self) -> Dict[str, Any]:
        return {'ok': True, 'connections': list(self._clients.keys())}

    def list_tables(self, connection_id: str) -> Dict[str, Any]:
        if connection_id not in self._clients: return {'ok': False, 'erreur': 'Non connecté'}
        try:
            client = self._clients[connection_id]
            # Assumes the URL specifies a default database, or we pick the first one
            db = self._get_db(client)
            tables = db.list_collection_names()
            return {'ok': True, 'tables': tables}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def _get_schema_snapshot_impl(self, connection_id: str, refresh: bool = False) -> Dict[str, Any]:
        if connection_id not in self._clients: return {'ok': False, 'erreur': 'Non connecté'}
        try:
            schema = {}
            client = self._clients[connection_id]
            db = self._get_db(client)
            collections = db.list_collection_names()
            
            for coll_name in collections:
                # Infer schema from a sample document
                sample = db[coll_name].find_one()
                if sample:
                    schema[coll_name] = [{"Field": k, "Type": type(v).__name__} for k, v in sample.items()]
                else:
                    schema[coll_name] = []
            return {'ok': True, 'schema': schema}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def execute_read_query(self, connection_id: str, query: Any, max_rows: int = 500, utilisateur_id: int = 0, base_id: int = 0) -> Dict[str, Any]:
        if connection_id not in self._clients: return {'ok': False, 'erreur': 'Non connecté'}
        
        try:
            if isinstance(query, str):
                query = json.loads(query)
                
            client = self._clients[connection_id]
            db = self._get_db(client)
            
            collection_name = query.get('collection')
            action = query.get('action', 'find')
            
            if action not in ['find', 'aggregate', 'count']:
                return {'ok': False, 'erreur': "Action de lecture non supportée."}
                
            coll = db[collection_name]
            
            if action == 'find':
                filter_doc = query.get('filter', {})
                projection = query.get('projection')
                sort = query.get('sort')
                limit = min(query.get('limit', max_rows), max_rows)
                
                cursor = coll.find(filter_doc, projection)
                if sort:
                    cursor = cursor.sort([(k, v) for k, v in sort.items()])
                cursor = cursor.limit(limit)
                
                rows = [json.loads(json.dumps(doc, cls=CustomJSONEncoder)) for doc in cursor]
                columns = list(rows[0].keys()) if rows else []
                return {'ok': True, 'columns': columns, 'rows': rows}
                
            elif action == 'aggregate':
                pipeline = query.get('pipeline', [])
                cursor = coll.aggregate(pipeline)
                rows = [json.loads(json.dumps(doc, cls=CustomJSONEncoder)) for doc in cursor]
                columns = list(rows[0].keys()) if rows else []
                return {'ok': True, 'columns': columns, 'rows': rows}
                
            elif action == 'count':
                filter_doc = query.get('filter', {})
                count = coll.count_documents(filter_doc)
                return {'ok': True, 'columns': ['count'], 'rows': [{'count': count}]}
                
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def preview_write_impact(self, connection_id: str, query: Any) -> Dict[str, Any]:
        if connection_id not in self._clients: return {'ok': False, 'erreur': 'Non connecté'}
        try:
            if isinstance(query, str):
                query = json.loads(query)
            
            action = query.get('action')
            if 'insert' in action:
                docs = query.get('document') or query.get('documents', [])
                count = len(docs) if isinstance(docs, list) else 1
                return {'ok': True, 'affected_rows': count}
            
            elif 'update' in action or 'delete' in action:
                client = self._clients[connection_id]
                db = self._get_db(client)
                coll = db[query.get('collection')]
                count = coll.count_documents(query.get('filter', {}))
                return {'ok': True, 'affected_rows': count}
                
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def execute_write_query(self, connection_id: str, query: Any, utilisateur_id: int, base_id: int, confirmed: bool = False) -> Dict[str, Any]:
        if not confirmed: return {'ok': False, 'erreur': "Confirmation requise."}
        if connection_id not in self._clients: return {'ok': False, 'erreur': 'Non connecté'}
        
        try:
            if isinstance(query, str):
                query = json.loads(query)
                
            client = self._clients[connection_id]
            db = self._get_db(client)
            coll = db[query.get('collection')]
            action = query.get('action')
            
            affected = 0
            # MongoDB ne supporte les transactions que sur replica sets.
            # On va utiliser une simple opération ici, mais pour une vraie app de prod, 
            # il faudrait utiliser client.start_session()
            
            if action == 'insertOne':
                res = coll.insert_one(query.get('document'))
                affected = 1 if res.inserted_id else 0
            elif action == 'updateOne':
                res = coll.update_one(query.get('filter'), query.get('update'))
                affected = res.modified_count
            elif action == 'deleteMany':
                res = coll.delete_many(query.get('filter'))
                affected = res.deleted_count
            else:
                return {'ok': False, 'erreur': f"Action d'écriture {action} non supportée par ce MCP minimaliste."}
                
            return {'ok': True, 'affected_rows': affected}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def render_chart(self, connection_id: str, chart_type: str, x: str, y: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        return {'ok': False}

    def get_write_history(self, connection_id: str) -> Dict[str, Any]:
        return {'ok': True, 'history': []}

    def is_mongodb(self) -> bool:
        return True
