# 🧠 QueryAI - Text-to-SQL & Text-to-MongoDB Desktop Application

QueryAI est une application de bureau moderne et intuitive développée en **Python 3** avec **PyQt6**. Elle permet aux utilisateurs métier et aux administrateurs de interagir avec diverses bases de données (relationnelles et non relationnelles) en utilisant uniquement le **langage naturel**. Grâce aux modèles d'intelligence artificielle les plus performants (GPT, Claude, Gemini, Qwen/DeepSeek via OpenRouter), l'application traduit instantanément vos questions textuelles en requêtes SQL optimisées ou en pipelines d'agrégation MongoDB, les exécute, et présente les résultats sous forme de graphiques interactifs et d'analyses (insights) automatisées.

---

## 🌟 Fonctionnalités Clés

### 👤 Rôle Utilisateur (Dashboard Principal)
* **Requêtes en Langage Naturel** : Tapez votre demande (ex. *"Donne-moi le top 5 des clients ayant dépensé le plus en 2025"*) et laissez l'IA générer la requête appropriée.
* **Support Multi-Dialectes** : Génère automatiquement du code adapté à la base cible :
  * **MySQL** (avec échappement par backticks, fonctions natives).
  * **PostgreSQL** (gestion de la casse, double quotes, types spécifiques).
  * **SQL Server** (syntaxe T-SQL, `TOP (n)`, crochets de protection).
  * **MongoDB** (pipelines d'agrégation complets au format JSON valide, `$unwind`, `$group`, etc.).
* **Exécution Directe** : Exécutez la requête en un clic et visualisez les résultats dans un tableau interactif ultra-rapide.
* **Visualisation Graphique** : Génération automatique de graphiques (secteurs, barres, courbes) basés sur la structure des colonnes retournées.
* **AI Insights (Analyses Métier)** : L'IA analyse les données retournées par la requête et rédige un résumé analytique clair et exploitable en français.
* **Export Universel** : Exportez les résultats en formats **CSV** ou **Excel (XLSX)**.

### 🔑 Rôle Administrateur (Gestion & Configuration)
* **Configuration des Bases de Données** : Ajoutez, modifiez et testez des connexions vers vos bases (MySQL, Postgres, SQL Server, MongoDB) en mode manuel ou par URL de connexion.
* **Chiffrement de Bout en Bout** : Tous les mots de passe et les chaînes de connexion de vos bases de données sont chiffrés avec l'algorithme fort **AES-256-GCM** avant d'être sauvegardés dans la base centrale.
* **Générateur de Schéma Métadonnées** : Importez ou modifiez la structure de vos tables/colonnes ou schémas JSON directement dans l'application pour fournir un contexte parfait à l'IA.
* **Gestion des Utilisateurs** : Créez des comptes pour vos collaborateurs et activez/désactivez-les instantanément.
* **Contrôle d'Accès Granulaire (Permissions)** : Associez les utilisateurs à des bases spécifiques avec des droits personnalisés (Lecture seule, Écriture, Admin).
* **Préférences Globales** : Thème visuel complet (Clair / Sombre) et traduction intégrale de l'interface en Français (FR) et Anglais (EN).

---

## ⚙️ Prérequis et Architecture

L'application utilise une architecture client-serveur locale organisée de la manière suivante :
* **Base de Données Centrale** : Une base de données centrale MySQL nommée `queryai_db` (installée par exemple via **XAMPP** ou un serveur autonome) sert à stocker de manière sécurisée les informations sur les utilisateurs, les connexions réseau, l'historique des requêtes et les clés API des services d'IA.
* **Cryptographie** : Un chiffrement symétrique AES-256-GCM protège toutes les informations d'identification à l'aide d'une clé maîtresse définie dans l'environnement.

---

## 🚀 Guide d'Installation Rapide

Suivez ces étapes simples pour démarrer l'application sur votre machine :

### 1. Cloner le projet et préparer l'environnement
Téléchargez les fichiers de votre projet dans un dossier local (par exemple `C:\xampp\htdocs\texte2sql`).

### 2. Installer les dépendances Python
Ouvrez votre terminal et exécutez la commande suivante pour installer toutes les dépendances requises (PyQt6, SQLAlchemy, pilotes de bases de données, outils d'analyse et cryptographie) :
```bash
pip install -r requirements.txt
```

### 3. Configurer le fichier d'environnement `.env`
Créez un fichier nommé `.env` à la racine du projet (un fichier modèle est fourni ci-dessous) :
```env
# Clé maître pour chiffrement AES-256-GCM (32 octets sous forme hexadécimale)
MASTER_ENCRYPTION_KEY=a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90

# Connexion MySQL de la base centrale (ex: XAMPP)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=queryai_db

# Service d'Intelligence Artificielle par défaut (gpt, claude, gemini, open_source)
DEFAULT_IA_SERVICE=open_source

# Clé API OpenRouter pour le modèle Open Source
OPENROUTER_API_KEY=votre_cle_openrouter_ici
```

> [!IMPORTANT]
> Ne poussez **jamais** votre fichier `.env` sur GitHub. Celui-ci est automatiquement ignoré grâce au fichier `.gitignore` afin de protéger vos secrets et votre clé maîtresse de chiffrement.

---

## 💻 Utilisation pas à pas

### Étape 1 : Démarrer MySQL (XAMPP)
Vérifiez que votre serveur MySQL local (comme XAMPP Control Panel) est démarré. L'application créera et configurera automatiquement la base de données centrale `queryai_db` et exécutera les migrations nécessaires au tout premier lancement.

### Étape 2 : Lancer l'application
Exécutez le script principal dans votre terminal :
```bash
python main.py
```

### Étape 3 : Premier lancement (Configuration Administrateur)
Au premier démarrage, l'application détectera qu'aucun administrateur n'est configuré et vous redirigera vers l'écran **Admin Setup**.
1. Renseignez votre prénom, nom, e-mail de connexion, votre mot de passe et le nom de votre entreprise.
2. Cliquez sur **Créer mon compte Admin**.
3. Vous serez redirigé vers l'écran de connexion standard. Connectez-vous avec vos identifiants fraîchement créés !

### Étape 4 : Utilisation par un Administrateur
Une fois connecté en tant qu'administrateur, utilisez la barre latérale pour configurer la plateforme :
1. **Bases de données** : Ajoutez vos bases de données de test ou de production. Entrez les identifiants ou l'URL de connexion, puis cliquez sur **Tester la connexion**. Dès que le test réussit, sauvegardez.
2. **Schéma de base** : Générez automatiquement le schéma ou copiez-y le descriptif JSON/SQL pour que l'IA comprenne la structure de vos tables.
3. **Utilisateurs** : Ajoutez des comptes pour les membres de votre équipe.
4. **Permissions** : Attribuez les droits d'accès à vos utilisateurs sur les bases configurées.

### Étape 5 : Utilisation par un Collaborateur (Requêteur)
Lorsqu'un utilisateur standard se connecte :
1. **Sélection de la base** : Il choisit parmi les bases de données sur lesquelles il a reçu des droits de lecture ou d'écriture.
2. **Saisie du message** : Il tape sa question (ex. : *"Affiche-moi le nombre de commandes par pays"*).
3. **Traduction & Exécution** : L'IA produit le code SQL/MongoDB. L'utilisateur clique sur **Exécuter**.
4. **Graphiques & Insights** :
   * L'onglet **Visualisation** trace instantanément un graphique parlant.
   * L'onglet **Insights** explique en bon français les conclusions analytiques des données reçues.
5. **Export** : Téléchargement du jeu de données en un clic.

---

## 🛠️ Dépannage et FAQ

#### 1. Erreur de connexion MySQL au démarrage
Si l'application se ferme avec un message d'erreur de base de données :
* Vérifiez que MySQL est bien démarré sur le port `3306` dans XAMPP.
* Vérifiez les configurations `MYSQL_HOST` et `MYSQL_PORT` dans votre fichier `.env`.

#### 2. Pilote SQL Server manquant sur Windows
Pour interagir avec des bases SQL Server, l'application requiert le pilote ODBC officiel de Microsoft. 
* Si une erreur `pyodbc.Error` survient, téléchargez et installez le **Microsoft ODBC Driver for SQL Server** gratuit sur le site de Microsoft.

---

## 🔒 Sécurité et Bonnes Pratiques
* **Clé Maîtresse** : La `MASTER_ENCRYPTION_KEY` du fichier `.env` est critique. Si vous perdez cette clé, vous ne pourrez plus déchiffrer les identifiants de vos bases de données enregistrées. Changez la clé générique fournie en exemple par une clé aléatoire forte en production.
* **Identifiants en dur** : Évitez à tout prix d'écrire des jetons d'accès ou mots de passe directement dans vos codes sources Python. Utilisez toujours le mécanisme de variables d'environnement (`os.environ`) déjà en place.
