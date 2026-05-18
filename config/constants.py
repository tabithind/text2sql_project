URL_TEMPLATES = {
    'mysql'     : 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}',
    'postgresql': 'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}',
    'mongodb'   : 'mongodb://{user}:{password}@{host}:{port}/{database}',
    'sqlserver' : 'mssql+pyodbc://{user}:{password}@{host}:{port}/{database}'
                  '?driver=ODBC+Driver+17+for+SQL+Server'
}

PORTS_DEFAUT = {
    'mysql'     : 3306,
    'postgresql': 5432,
    'mongodb'   : 27017,
    'sqlserver' : 1433
}

URL_PLACEHOLDERS = {
    'mysql'     : 'mysql://user:password@host:3306/database',
    'postgresql': 'postgresql://user:password@host:5432/database',
    'mongodb'   : 'mongodb://user:password@host:27017/database',
    'sqlserver' : 'mssql+pyodbc://user:password@host:1433/database?driver=ODBC+Driver+17+for+SQL+Server'
}

COULEURS_DB = {
    'mysql'     : '#00758F',
    'postgresql': '#336791',
    'mongodb'   : '#47A248',
    'sqlserver' : '#CC2927'
}

SERVICES_IA = {
    'gpt'    : 'https://api.openai.com/v1/chat/completions',
    'claude' : 'https://api.anthropic.com/v1/messages',
    'gemini' : 'https://generativelanguage.googleapis.com/v1/generate'
}

# Configuration des champs pour chaque type de base de données
DB_FIELD_CONFIG = {
    'mysql': {
        'nom': 'MySQL',
        'icon': '🐬',
        'champs_obligatoires': ['host', 'port', 'database', 'user', 'password'],
        'champs_optionnels': ['charset'],
        'port_defaut': 3306,
        'info': 'MySQL est une base relationnelle populaire. Assurez-vous que le serveur MySQL est en cours d\'exécution.'
    },
    'postgresql': {
        'nom': 'PostgreSQL',
        'icon': '🐘',
        'champs_obligatoires': ['host', 'port', 'database', 'user', 'password'],
        'champs_optionnels': ['sslmode'],
        'port_defaut': 5432,
        'info': 'PostgreSQL est une base relationnelle puissante avec support SSL/TLS.'
    },
    'mongodb': {
        'nom': 'MongoDB',
        'icon': '🍃',
        'champs_obligatoires': ['host', 'port'],
        'champs_optionnels': ['database', 'user', 'password', 'authSource', 'replSet'],
        'port_defaut': 27017,
        'info': 'MongoDB est une base de données NoSQL. Les identifiants sont optionnels si l\'authentification est désactivée.'
    },
    'sqlserver': {
        'nom': 'SQL Server',
        'icon': '💾',
        'champs_obligatoires': ['host', 'database', 'user', 'password'],
        'champs_optionnels': ['port', 'encrypt', 'trustServerCertificate'],
        'port_defaut': 1433,
        'info': 'SQL Server nécessite un driver ODBC (ODBC Driver 17 ou 18 recommandé).'
    }
}

# Descriptions des champs
FIELD_DESCRIPTIONS = {
    'host': {'label': 'Host', 'placeholder': 'localhost ou adresse IP', 'type': 'text'},
    'server': {'label': 'Serveur', 'placeholder': 'localhost ou adresse IP', 'type': 'text'},
    'port': {'label': 'Port', 'placeholder': '3306', 'type': 'number'},
    'database': {'label': 'Base de données', 'placeholder': 'nom_base', 'type': 'text'},
    'user': {'label': 'Utilisateur', 'placeholder': 'root', 'type': 'text'},
    'password': {'label': 'Mot de passe', 'placeholder': '', 'type': 'password'},
    'charset': {'label': 'Charset', 'placeholder': 'utf8mb4', 'type': 'text'},
    'sslmode': {'label': 'Mode SSL', 'placeholder': 'disable, allow, prefer, require', 'type': 'text'},
    'authSource': {'label': 'Auth Source', 'placeholder': 'admin', 'type': 'text'},
    'replSet': {'label': 'Replica Set', 'placeholder': 'replica0', 'type': 'text'},
    'encrypt': {'label': 'Chiffrer (yes/no)', 'placeholder': 'yes', 'type': 'text'},
    'trustServerCertificate': {'label': 'Faire confiance au certificat (yes/no)', 'placeholder': 'no', 'type': 'text'}
}
