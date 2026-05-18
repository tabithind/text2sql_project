import pymysql
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

MYSQL_CONFIG = {
    'host'    : settings.MYSQL_HOST,
    'port'    : settings.MYSQL_PORT,
    'user'    : settings.MYSQL_USER,
    'password': settings.MYSQL_PASSWORD,
    'charset' : 'utf8mb4'
}

DB_NAME = settings.MYSQL_DATABASE

SQL_SCRIPT = """
-- ============================================================
-- Table : admins
-- Un admin par entreprise cliente
-- ============================================================

CREATE TABLE IF NOT EXISTS admins (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    prenom        VARCHAR(100) NOT NULL,
    nom           VARCHAR(100) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    entreprise    VARCHAR(150) NOT NULL,
    actif         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table : utilisateurs
-- Créés par l'admin, liés via admin_id
-- ============================================================

CREATE TABLE IF NOT EXISTS utilisateurs (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    admin_id      INT NOT NULL,
    prenom        VARCHAR(100) NOT NULL,
    nom           VARCHAR(100) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    actif         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table : bases_de_donnees
-- Bases connectées par l'admin (credentials chiffrés AES-256-GCM)
-- ============================================================

CREATE TABLE IF NOT EXISTS bases_de_donnees (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    admin_id       INT NOT NULL,
    nom            VARCHAR(150) NOT NULL,
    type           ENUM('mysql','postgresql','mongodb','sqlserver') NOT NULL,
    mode_connexion ENUM('url','manuel') NOT NULL DEFAULT 'manuel',

    -- Mode URL (chiffrée AES-256-GCM)
    url_connexion  TEXT,
    url_iv         VARCHAR(64),
    url_auth_tag   VARCHAR(64),

    -- Mode Manuel (password chiffré AES-256-GCM)
    host           VARCHAR(255),
    port           INT,
    nom_base       VARCHAR(150),
    utilisateur_db VARCHAR(100),
    password_db    TEXT,
    pw_iv          VARCHAR(64),
    pw_auth_tag    VARCHAR(64),

    actif          BOOLEAN NOT NULL DEFAULT TRUE,
    schema_db      LONGTEXT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table : permissions
-- Droits d'accès utilisateur ↔ base de données
-- ============================================================

CREATE TABLE IF NOT EXISTS permissions (
    id                 INT PRIMARY KEY AUTO_INCREMENT,
    utilisateur_id     INT NOT NULL,
    base_de_donnees_id INT NOT NULL,
    type_acces         ENUM('lecture','ecriture','admin') NOT NULL DEFAULT 'lecture',
    attribue_le        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_perm (utilisateur_id, base_de_donnees_id),
    FOREIGN KEY (utilisateur_id)     REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (base_de_donnees_id) REFERENCES bases_de_donnees(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table : services_ia
-- Services IA disponibles (partagé global — services fixes)
-- ============================================================

CREATE TABLE IF NOT EXISTS services_ia (
    id       INT PRIMARY KEY AUTO_INCREMENT,
    nom      VARCHAR(50) NOT NULL,
    type     VARCHAR(10) NOT NULL DEFAULT 'API',
    endpoint VARCHAR(500) NOT NULL,
    actif    BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Données initiales des services (insérées une seule fois)
INSERT IGNORE INTO services_ia (nom, type, endpoint) VALUES
('gpt',    'API', 'https://api.openai.com/v1/chat/completions'),
('claude', 'API', 'https://api.anthropic.com/v1/messages'),
('gemini', 'API', 'https://generativelanguage.googleapis.com/v1/generate'),
('open_source', 'API', 'https://openrouter.ai/api/v1/chat/completions');

-- ============================================================
-- Table : cles_api
-- Clés API des utilisateurs (chiffrées AES-256-GCM)
-- Une clé par utilisateur par service IA
-- ============================================================

CREATE TABLE IF NOT EXISTS cles_api (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    utilisateur_id INT NOT NULL,
    service_ia_id  INT NOT NULL,
    cle_chiffree   TEXT NOT NULL,
    iv             VARCHAR(64) NOT NULL,
    auth_tag       VARCHAR(64) NOT NULL,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_cle (utilisateur_id, service_ia_id),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (service_ia_id)  REFERENCES services_ia(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table : requetes
-- Historique de toutes les requêtes soumises
-- ============================================================

CREATE TABLE IF NOT EXISTS requetes (
    id                 INT PRIMARY KEY AUTO_INCREMENT,
    utilisateur_id     INT NOT NULL,
    base_de_donnees_id INT NOT NULL,
    service_ia_id      INT NOT NULL,
    texte_naturel      TEXT NOT NULL,
    sql_genere         TEXT,
    statut             ENUM('en_attente','succes','echec') NOT NULL DEFAULT 'en_attente',
    date_creation      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (utilisateur_id)     REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (base_de_donnees_id) REFERENCES bases_de_donnees(id),
    FOREIGN KEY (service_ia_id)      REFERENCES services_ia(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table : resultats
-- Résultats des requêtes (relation 1:1 avec requetes)
-- ============================================================

CREATE TABLE IF NOT EXISTS resultats (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    requete_id INT NOT NULL UNIQUE,
    contenu    LONGTEXT NOT NULL,
    format     ENUM('JSON','CSV','Excel') NOT NULL DEFAULT 'JSON',
    genere_le  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requete_id) REFERENCES requetes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table : settings
-- Préférences par utilisateur ou par admin (thème, langue...)
-- ============================================================

CREATE TABLE IF NOT EXISTS settings (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    utilisateur_id INT,
    admin_id       INT,
    cle            VARCHAR(100) NOT NULL,
    valeur         TEXT NOT NULL,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id)       REFERENCES admins(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

def run_migrations():
    """
    Crée la base queryai_db et toutes ses tables si elles n'existent pas.
    Appelé automatiquement au démarrage de l'application.
    """
    try:
        # Connexion sans spécifier de base (pour créer queryai_db)
        conn = pymysql.connect(**MYSQL_CONFIG)
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS {DB_NAME} "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.select_db(DB_NAME)

        # Exécuter tout le script SQL de création des tables
        with conn.cursor() as cur:
            for statement in SQL_SCRIPT.strip().split(';'):
                stmt = statement.strip()
                if stmt:
                    cur.execute(stmt)
        conn.commit()

        # S'assurer que la colonne schema_db existe pour les tables déjà créées
        with conn.cursor() as cur:
            cur.execute("SHOW COLUMNS FROM bases_de_donnees LIKE 'schema_db'")
            if not cur.fetchone():
                logger.info("Ajout de la colonne schema_db dans la table bases_de_donnees...")
                cur.execute("ALTER TABLE bases_de_donnees ADD COLUMN schema_db LONGTEXT NULL")
                conn.commit()

            # S'assurer que la colonne nom de la table services_ia n'est plus un ENUM strict
            cur.execute("SHOW COLUMNS FROM services_ia LIKE 'nom'")
            col_info = cur.fetchone()
            if col_info:
                # col_info peut être un tuple ou un dictionnaire selon le cursorclass utilisé
                col_type = col_info['Type'] if isinstance(col_info, dict) else col_info[1]
                if col_type.startswith('enum'):
                    logger.info("Modification de la colonne nom dans services_ia de ENUM à VARCHAR...")
                    cur.execute("ALTER TABLE services_ia MODIFY COLUMN nom VARCHAR(50) NOT NULL")
                    conn.commit()

            # Insérer 'open_source' s'il n'existe pas
            cur.execute("SELECT id FROM services_ia WHERE nom = 'open_source'")
            if not cur.fetchone():
                logger.info("Ajout du service open_source dans la table services_ia...")
                cur.execute(
                    "INSERT INTO services_ia (nom, type, endpoint) VALUES (%s, %s, %s)",
                    ('open_source', 'API', 'https://openrouter.ai/api/v1/chat/completions')
                )
                conn.commit()

        conn.close()
        logger.info(f"✅ Base {DB_NAME} initialisée avec succès.")

    except Exception as e:
        logger.error(f"❌ Erreur migration : {e}")
        raise
