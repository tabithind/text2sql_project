from typing import Any, Dict, List, Optional
from services.mcp.base_mcp import BaseMCP
from services.database_connectors import ConnectorFactory

class MySQLMCP(BaseMCP):
    def __init__(self):
        self._connections: Dict[str, Any] = {}
        self.connector = ConnectorFactory.get_connector('mysql')

    def connect(self, url: str) -> Dict[str, Any]:
        try:
            conn = self.connector.connect(url)
            
            import hashlib
            conn_id = hashlib.md5(url.encode()).hexdigest()
            self._connections[conn_id] = conn
            return {'ok': True, 'connection_id': conn_id}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def disconnect(self, connection_id: str) -> Dict[str, Any]:
        if connection_id in self._connections:
            self.connector.close(self._connections[connection_id])
            del self._connections[connection_id]
        return {'ok': True}

    def list_databases(self, connection_id: str) -> Dict[str, Any]:
        if connection_id not in self._connections: return {'ok': False, 'erreur': 'Non connecté'}
        try:
            conn = self._connections[connection_id]
            with conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                # Using DictCursor, so rows are dicts
                dbs = [row['Database'] if 'Database' in row else list(row.values())[0] for row in cursor.fetchall()]
                return {'ok': True, 'databases': dbs}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def list_connections(self) -> Dict[str, Any]:
        return {'ok': True, 'connections': list(self._connections.keys())}

    def list_tables(self, connection_id: str) -> Dict[str, Any]:
        if connection_id not in self._connections: return {'ok': False, 'erreur': 'Non connecté'}
        try:
            conn = self._connections[connection_id]
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [list(row.values())[0] for row in cursor.fetchall()]
                return {'ok': True, 'tables': tables}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def _get_schema_snapshot_impl(self, connection_id: str, refresh: bool = False) -> Dict[str, Any]:
        if connection_id not in self._connections: return {'ok': False, 'erreur': 'Non connecté'}
        try:
            schema = {}
            conn = self._connections[connection_id]
            with conn.cursor() as cursor:
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
                            "Default": c.get('Default'), 
                            "Extra": c.get('Extra')
                        }
                        for c in cols
                    ]
            return {'ok': True, 'schema': schema}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def execute_read_query(self, connection_id: str, query: str, max_rows: int = 500, utilisateur_id: int = 0, base_id: int = 0) -> Dict[str, Any]:
        if connection_id not in self._connections: return {'ok': False, 'erreur': 'Non connecté'}
        
        q_lower = query.lower().strip()
        if not q_lower.startswith('select') and not q_lower.startswith('show') and not q_lower.startswith('describe'):
            return {'ok': False, 'erreur': "Seules les requêtes SELECT/SHOW sont autorisées pour la lecture."}

        try:
            if "limit" not in q_lower:
                query = f"{query.rstrip(';')} LIMIT {max_rows}"
                
            conn = self._connections[connection_id]
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if not rows:
                    columns = []
                    formatted_rows = []
                else:
                    columns = list(rows[0].keys())
                    formatted_rows = [list(row.values()) for row in rows]
                return {'ok': True, 'columns': columns, 'rows': formatted_rows}
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    def preview_write_impact(self, connection_id: str, query: str) -> Dict[str, Any]:
        if connection_id not in self._connections: return {'ok': False, 'erreur': 'Non connecté'}
        
        q_lower = query.lower().strip()
        if q_lower.startswith('delete') or q_lower.startswith('update'):
            try:
                conn = self._connections[connection_id]
                conn.begin()
                with conn.cursor() as cursor:
                    affected = cursor.execute(query)
                conn.rollback()
                return {'ok': True, 'affected_rows': affected}
            except Exception as e:
                # rollback in case of error
                try:
                    conn.rollback()
                except:
                    pass
                return {'ok': False, 'erreur': str(e)}
        return {'ok': True, 'affected_rows': 'Inconnu pour cette opération'}

    def execute_write_query(self, connection_id: str, query: str, utilisateur_id: int, base_id: int, confirmed: bool = False) -> Dict[str, Any]:
        if not confirmed:
            return {'ok': False, 'erreur': "Confirmation requise pour exécuter l'écriture."}
        if connection_id not in self._connections: return {'ok': False, 'erreur': 'Non connecté'}

        try:
            conn = self._connections[connection_id]
            conn.begin()
            with conn.cursor() as cursor:
                affected = cursor.execute(query)
            conn.commit()
            return {'ok': True, 'affected_rows': affected}
        except Exception as e:
            try:
                conn.rollback()
            except:
                pass
            return {'ok': False, 'erreur': str(e)}

    def render_chart(self, connection_id: str, chart_type: str, x: str, y: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        return {'ok': False, 'erreur': "Graphiques gérés par ChartService global"}

    def get_write_history(self, connection_id: str) -> Dict[str, Any]:
        return {'ok': True, 'history': []}

    def is_mongodb(self) -> bool:
        return False
