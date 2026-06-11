import os
import json
import requests
import re
from database.connection import get_connection
from services.crypto_service import CryptoService

class IAService:
    @staticmethod
    def save_api_key(utilisateur_id: int, nom_service: str, api_key: str) -> dict:
        """Sauvegarde/met à jour la clé API de l'utilisateur (chiffrée)."""
        try:
            # Chiffrer la clé
            encrypted = CryptoService.chiffrer(api_key)
            
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    # Récupérer le service_ia_id
                    cur.execute("SELECT id FROM services_ia WHERE nom = %s", (nom_service,))
                    service_row = cur.fetchone()
                    if not service_row:
                        return {'ok': False, 'erreur': f"Service {nom_service} non trouvé."}
                    
                    service_ia_id = service_row['id']
                    
                    # Vérifier si la clé existe déjà
                    cur.execute(
                        "SELECT id FROM cles_api WHERE utilisateur_id = %s AND service_ia_id = %s",
                        (utilisateur_id, service_ia_id)
                    )
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update
                        cur.execute("""
                            UPDATE cles_api 
                            SET cle_chiffree = %s, iv = %s, auth_tag = %s
                            WHERE utilisateur_id = %s AND service_ia_id = %s
                        """, (encrypted['cle_chiffree'], encrypted['iv'], encrypted['auth_tag'], 
                              utilisateur_id, service_ia_id))
                    else:
                        # Insert
                        cur.execute("""
                            INSERT INTO cles_api (utilisateur_id, service_ia_id, cle_chiffree, iv, auth_tag)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (utilisateur_id, service_ia_id, encrypted['cle_chiffree'], 
                              encrypted['iv'], encrypted['auth_tag']))
                    
                    conn.commit()
                    return {'ok': True}
            finally:
                conn.close()
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    @staticmethod
    def api_key_exists(utilisateur_id: int, nom_service: str) -> bool:
        """Vérifie si une clé API existe pour ce service et cet utilisateur."""
        try:
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT c.id FROM cles_api c
                        JOIN services_ia s ON c.service_ia_id = s.id
                        WHERE c.utilisateur_id = %s AND s.nom = %s
                    """, (utilisateur_id, nom_service))
                    return cur.fetchone() is not None
            finally:
                conn.close()
        except:
            return False

    @staticmethod
    def delete_api_key(utilisateur_id: int, nom_service: str) -> dict:
        """Supprime la clé API de l'utilisateur."""
        try:
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    # Récupérer le service_ia_id
                    cur.execute("SELECT id FROM services_ia WHERE nom = %s", (nom_service,))
                    service_row = cur.fetchone()
                    if not service_row:
                        return {'ok': False, 'erreur': f"Service {nom_service} non trouvé."}
                    
                    service_ia_id = service_row['id']
                    
                    # Supprimer la clé
                    cur.execute(
                        "DELETE FROM cles_api WHERE utilisateur_id = %s AND service_ia_id = %s",
                        (utilisateur_id, service_ia_id)
                    )
                    
                    conn.commit()
                    return {'ok': True}
            finally:
                conn.close()
        except Exception as e:
            return {'ok': False, 'erreur': str(e)}

    @staticmethod
    def detecter_intention(texte: str) -> str:
        """Détecte l'intention de la requête en langage naturel."""
        t = texte.lower().strip()
        
        mots_schema = [
            'schema', 'structure', 'tables', 'colonnes', 'columns',
            'voir la base', 'show tables', 'describe', 'liste des tables'
        ]
        mots_insert = [
            'ajouter', 'insérer', 'créer', 'nouveau', 'nouvelle',
            'add', 'insert', 'create', 'new record'
        ]
        mots_update = [
            'modifier', 'mettre à jour', 'changer', 'corriger', 'éditer',
            'update', 'modify', 'change', 'edit', 'set'
        ]
        mots_delete = [
            'supprimer', 'effacer', 'enlever', 'retirer',
            'delete', 'remove', 'erase', 'drop record'
        ]

        if any(m in t for m in mots_schema): return 'schema'
        if any(m in t for m in mots_insert): return 'insert'
        if any(m in t for m in mots_update): return 'update'
        if any(m in t for m in mots_delete): return 'delete'
        return 'select'

    @staticmethod
    def get_api_key(utilisateur_id: int, nom_service: str) -> str:
        """Récupère et déchiffre la clé API de l'utilisateur."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT c.cle_chiffree, c.iv, c.auth_tag 
                    FROM cles_api c
                    JOIN services_ia s ON c.service_ia_id = s.id
                    WHERE c.utilisateur_id = %s AND s.nom = %s
                """, (utilisateur_id, nom_service))
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Clé API non configurée pour le service {nom_service}.")
                return CryptoService.dechiffrer(row['cle_chiffree'], row['iv'], row['auth_tag'])
        finally:
            conn.close()

    @staticmethod
    def _call_gpt(api_key: str, full_prompt: str, is_mongodb: bool) -> str:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        system_content = "You are a professional MongoDB aggregation expert." if is_mongodb else "You are a professional senior database engineer."
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.0
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()

    @staticmethod
    def _call_claude(api_key: str, full_prompt: str, is_mongodb: bool) -> str:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        system_content = "You are a professional MongoDB aggregation expert." if is_mongodb else "You are a professional senior database engineer."
        payload = {
            "model": "claude-opus-4-1",
            "max_tokens": 1024,
            "system": system_content,
            "messages": [
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.0
        }
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['content'][0]['text'].strip()

    @staticmethod
    def _call_gemini(api_key: str, full_prompt: str, is_mongodb: bool) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.0}
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()

    @staticmethod
    def generate_query(utilisateur_id: int, nom_service: str, user_query: str, schema: str = "", is_mongodb: bool = False, base_id: int = None) -> str:
        """Génère une requête via le service IA sélectionné en utilisant un prompt d'ingénierie spécialisé."""
        try:
            api_key = IAService.get_api_key(utilisateur_id, nom_service)
        except Exception as e:
            if nom_service == 'open_source':
                api_key = os.environ.get('OPENROUTER_API_KEY', '')
            else:
                raise e
        
        db_type = 'mongodb' if is_mongodb else 'mysql'
        db_name = 'database'
        schema_str = schema
        
        if base_id is not None:
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT nom, type, nom_base, schema_db FROM bases_de_donnees WHERE id = %s", (base_id,))
                    row = cur.fetchone()
                    if row:
                        db_type = row['type']
                        db_name = row['nom_base'] or row['nom']
                        is_mongodb = (db_type.lower() == 'mongodb')
                        if row['schema_db']:
                            try:
                                schema_dict = json.loads(row['schema_db'])
                                schema_str = json.dumps(schema_dict, indent=2, ensure_ascii=False)
                            except:
                                schema_str = str(row['schema_db'])
                        else:
                            schema_str = schema
            finally:
                conn.close()

        # Build prompt using custom prompt engineering rules
        if is_mongodb:
            # MongoDB Aggregation Prompt
            full_prompt = f"""You are a MongoDB query and aggregation pipeline expert.

DATABASE : {db_name}

COLLECTIONS SCHEMA
{schema_str}

USER REQUEST : {user_query}

RULES (follow strictly)
1) Output ONLY a valid JSON object matching the exact structure below. No explanation, no markdown, no code fences.
2) Structure for simple filter/find queries:
{{
  "collection": "<collection_name>",
  "action": "find",
  "filter": {{ <filter_fields> }}
}}
3) Structure for aggregation/grouping/nested arrays:
{{
  "collection": "<collection_name>",
  "action": "aggregate",
  "pipeline": [ <pipeline_stages> ]
}}
4) To access fields inside an array-of-objects:
   - First stage: {{"$unwind": "$arrayField"}}
   - Then use dot-notation: "$arrayField.subField"
5) Always use the exact collection and field names shown in the schema.
6) If the request asks for a chart / distribution / grouping, always use a pipeline
   that returns exactly 2 fields: one label (_id or renamed) and one numeric value.
7) Add {{"$sort": ...}} stage at the end of pipeline when ordering makes sense.

OUTPUT: JSON only."""
        else:
            # SQL Database Prompt
            dialect = "MySQL"
            rules = "1) Use backticks (`) for escaping table/column names only if they are reserved keywords or contain spaces.\n2) Use standard MySQL operators and functions (e.g., NOW(), DATE(), CONCAT())."
            
            if db_type.lower() == 'postgresql':
                dialect = "PostgreSQL"
                rules = "1) Use double quotes (\") for escaping table/column names if they contain uppercase letters, spaces or special characters.\n2) Use standard PostgreSQL operators and functions (e.g., CURRENT_TIMESTAMP, NOW(), TO_CHAR())."
            elif db_type.lower() == 'sqlserver':
                dialect = "SQL Server"
                rules = "1) Use square brackets ([]) for escaping table/column names if they contain special characters or spaces.\n2) Use standard T-SQL operators and functions (e.g., GETDATE(), CONVERT())."
                
            full_prompt = f"""You are a senior {dialect} database engineer.

TASK: Convert the user's natural-language request into ONE safe, optimized SELECT query.

CONTEXT
Database: {db_name}

SCHEMA (authoritative; do not guess anything not listed here)
{schema_str}

USER REQUEST
{user_query}

HARD RULES (must follow)
1) Output ONLY the SQL query OR a clarification request. Use CLARIFY only if required.
2) Allowed: exactly ONE statement starting with SELECT (or WITH...SELECT). No semicolons.
3) Use ONLY tables/columns that exist in SCHEMA.
   If missing/ambiguous -> output: CLARIFY: <one short question>
4) Always quote identifiers with special chars or reserved words.
5) {("Use TOP (n) instead of LIMIT." if db_type.lower() == "sqlserver" else "Use LIMIT n.")}
6) Prefer explicit JOINs with ON conditions; never use implicit joins.
7) Never use SQL keywords as table aliases.
8) If filtering by text: use = for exact match unless partial match implied (LIKE).
9) For chart requests: return category + metric columns (not just IDs)

CHART-FRIENDLY OUTPUT
- Pie chart without metric -> return category + COUNT(*)
- Distribution by category -> GROUP BY category with COUNT(*) or SUM(metric)
- Prefer 2 columns for charts with meaningful AS aliases

SYNTAX RULES for {dialect}:
{rules}

OUTPUT: SQL query only, or CLARIFY: <question>."""

        try:
            if nom_service == 'gpt':
                result = IAService._call_gpt(api_key, full_prompt, is_mongodb)
            elif nom_service == 'claude':
                result = IAService._call_claude(api_key, full_prompt, is_mongodb)
            elif nom_service == 'gemini':
                result = IAService._call_gemini(api_key, full_prompt, is_mongodb)
            elif nom_service == 'open_source':
                # 1. Generator step using Qwen-2.5-7B
                generated = IAService._call_openrouter(api_key, "qwen/qwen-2.5-7b-instruct", full_prompt)
                generated_cleaned = IAService.clean_sql(generated)
                
                # 2. Corrector step using DeepSeek-Chat
                if is_mongodb:
                    correction_prompt = IAService.build_correction_prompt_mongodb(schema_str, generated_cleaned)
                else:
                    correction_prompt = IAService.build_correction_prompt_sql(schema_str, generated_cleaned)
                
                corrected = IAService._call_openrouter(api_key, "deepseek/deepseek-chat", correction_prompt)
                corrected_query, insight = IAService.parse_corrector_response(corrected)
                
                result = IAService.clean_sql(corrected_query)
            else:
                raise ValueError(f"Service IA {nom_service} non supporté.")
            
            # Remove possible markdown blocks
            result_strip = result.strip()
            if result_strip.startswith("```"):
                lines = result_strip.split('\n')
                if len(lines) >= 3:
                    result_strip = '\n'.join(lines[1:-1]).strip()
            return result_strip
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'appel au service {nom_service} : {e}")

    @staticmethod
    def generate_insights(utilisateur_id: int, nom_service: str, user_query: str, query: str, result_data: dict) -> str:
        """Génère des analyses (insights) en français à partir des résultats de la requête."""
        try:
            try:
                api_key = IAService.get_api_key(utilisateur_id, nom_service)
            except Exception as e:
                if nom_service == 'open_source':
                    api_key = os.environ.get('OPENROUTER_API_KEY', '')
                else:
                    raise e
            
            columns = result_data.get('columns', [])
            rows = result_data.get('rows', [])
            
            # Limiter le nombre de lignes pour ne pas surcharger le prompt
            sample_rows = rows[:50]
            
            prompt = f"""En tant qu'expert en analyse de données de haut niveau, ton rôle est de fournir des aperçus stratégiques (insights) clairs et concis basés sur les résultats d'une requête de base de données.

QUESTION DE L'UTILISATEUR:
"{user_query}"

REQUÊTE EXÉCUTÉE:
`{query}`

RÉSULTATS DE LA REQUÊTE (Premières lignes, max 50):
Colonnes: {columns}
Lignes: {sample_rows}

CONSIGNES:
1) Analyse les données et résume les points clés, tendances majeures, ou anomalies notables.
2) Fais le lien avec la question d'origine de l'utilisateur.
3) Sois très synthétique (environ 3 à 5 puces ou un court paragraphe).
4) Rédige des explications claires et faciles à comprendre pour un décideur métier.
5) Réponds impérativement en français, avec un ton professionnel et engageant.

OUTPUT: Rédige directement l'analyse en Markdown standard, sans introduction inutile ni formules de politesse."""

            if nom_service == 'gpt':
                return IAService._call_gpt(api_key, prompt, False)
            elif nom_service == 'claude':
                return IAService._call_claude(api_key, prompt, False)
            elif nom_service == 'gemini':
                return IAService._call_gemini(api_key, prompt, False)
            elif nom_service == 'open_source':
                return IAService._call_openrouter(api_key, "deepseek/deepseek-chat", prompt)
            else:
                return "Service IA non supporté pour la génération d'insights."
        except Exception as e:
            return f"Impossible de générer des insights : {str(e)}"

    @staticmethod
    def _call_openrouter(api_key: str, model: str, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise Exception(result["error"])
        return result['choices'][0]['message']['content'].strip()

    @staticmethod
    def build_correction_prompt_sql(schema: str, sql_query: str) -> str:
        return f"""You are an advanced SQL validator and optimizer.

You must validate:
1. Table names (must exist in schema)
2. Column names (must exist in schema)
3. Column TYPES compatibility with SQL operations
4. Query logic correctness
5. Remove duplicates if needed
6. Fix aggregation issues if needed

----------------------------------------
IMPORTANT TYPE RULES:
- numeric / integer:
  -> allowed in: SUM, AVG, COUNT, >, <, =
- text / varchar:
  -> allowed in: LIKE, =, GROUP BY, CONCAT
  -> NOT meaningful for SUM or AVG
- date / timestamp:
  -> allowed in: comparisons (> < BETWEEN)
- boolean:
  -> only = TRUE / FALSE

----------------------------------------
STRICT RULES:
- If operation is incompatible with column type → FIX IT
- Never assume type correctness without checking schema
- Always rewrite query if needed
- Preserve original intent
- If duplicates possible → add DISTINCT or GROUP BY

OUTPUT FORMAT:
Return ONLY SQL query (no explanation, no markdown)

DATABASE SCHEMA:
{schema}

SQL QUERY:
{sql_query}

FINAL CORRECT SQL:"""

    @staticmethod
    def build_correction_prompt_mongodb(schema: str, mongodb_query: str) -> str:
        return f"""You are an advanced MongoDB query validator and optimizer.

You must validate:
1. Collection names (must exist in schema)
2. Field names (must exist in schema)
3. Pipeline structure (must be valid JSON, aggregation stages or find filters must be correct)
4. Ensure logical correctness

OUTPUT FORMAT:
Return ONLY valid JSON query (no explanation, no markdown)

DATABASE SCHEMA:
{schema}

MONGODB QUERY:
{mongodb_query}

FINAL CORRECT MONGODB QUERY:"""

    @staticmethod
    def clean_sql(text: str) -> str:
        if text is None:
            return None
        
        # 1. Search for markdown code blocks (e.g. ```sql ... ``` or ```json ... ``` or ``` ... ```)
        match = re.search(r"```(?:sql|json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # 2. Extract starting from the first SQL/MongoDB query keyword if there's conversational text
        sql_keywords = r"\b(SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|DESCRIBE|CREATE|ALTER|DROP|db\.)\b|{"
        match_kw = re.search(sql_keywords, text, re.IGNORECASE)
        if match_kw:
            return text[match_kw.start():].strip()
            
        # Fallback to standard replace
        cleaned = text.replace("```sql", "").replace("```json", "").replace("```", "")
        return cleaned.strip()

    @staticmethod
    def parse_corrector_response(text: str) -> tuple:
        if text is None:
            return None, None
        
        # 1. Clean using the robust clean_sql method
        cleaned = IAService.clean_sql(text)
        
        # 2. Try JSON parsing
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and ("sql" in data or "insight" in data):
                return data.get("sql"), data.get("insight")
            return cleaned, "Query processes data from database."
        except Exception:
            return cleaned, "Query processes data from database."
