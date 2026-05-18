from services.mcp.base_mcp import BaseMCP
from services.mcp.mysql_mcp import MySQLMCP
from services.mcp.postgresql_mcp import PostgreSQLMCP
from services.mcp.mongodb_mcp import MongoDBMCP
from services.mcp.sqlserver_mcp import SQLServerMCP

MCP_MAP = {
    'mysql': MySQLMCP,
    'postgresql': PostgreSQLMCP,
    'mongodb': MongoDBMCP,
    'sqlserver': SQLServerMCP
}

class MCPRouter:
    _instances = {}

    @classmethod
    def get(cls, type_db: str) -> BaseMCP:
        """
        Retourne l'instance MCP correspondant au type de base.
        Singleton par type.
        """
        type_db = type_db.lower().strip()
        if type_db not in MCP_MAP:
            raise ValueError(f"Type de base non supporté : {type_db}")
        if type_db not in cls._instances:
            cls._instances[type_db] = MCP_MAP[type_db]()
        return cls._instances[type_db]
