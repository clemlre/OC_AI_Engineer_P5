# Base de données - API Prédiction d'Attrition

> Documentation complète de la couche base de données : schéma relationnel, système d'authentification, architecture dual-engine, initialisation des données et sécurité.

---

## 1. Schéma relationnel

### Diagramme ERD

```mermaid
erDiagram
    employees {
        int id PK
        int age
        string genre
        int revenu_mensuel
        string statut_marital
        string departement
        string poste
        int nombre_experiences_precedentes
        int annee_experience_totale
        int annees_dans_l_entreprise
        int annees_dans_le_poste_actuel
        int satisfaction_employee_environnement
        int note_evaluation_precedente
        int niveau_hierarchique_poste
        int satisfaction_employee_nature_travail
        int satisfaction_employee_equipe
        int satisfaction_employee_equilibre_pro_perso
        int note_evaluation_actuelle
        string heure_supplementaires
        string augementation_salaire_precedente
        int nombre_participation_pee
        int nb_formations_suivies
        int distance_domicile_travail
        int niveau_education
        string domaine_etude
        string frequence_deplacement
        int annees_depuis_la_derniere_promotion
        int annes_sous_responsable_actuel
        string a_quitte_l_entreprise
        datetime created_at
    }

    predictions {
        int id PK
        json input_data
        int prediction
        float probability
        string model_version
        string api_key_used
        datetime created_at
    }

    api_keys {
        int id PK
        string key_hash UK
        string name
        bool is_active
        datetime created_at
    }

    api_keys ||--o{ predictions : "api_key_used référence le hash"
```

### Description des tables

#### `employees` - Dataset RH statique

28 colonnes de données + `id` (PK auto-incrémenté) + `created_at` (timestamp UTC). 1 470 lignes chargées depuis la fusion de 3 fichiers CSV. Cette table n'est pas modifiée par l'API (lecture seule implicite) ; elle sert de référentiel pour le dataset d'entraînement.

Colonnes notables :
- `age` (Integer) : âge de l'employé
- `genre` (String 10) : "F" ou "M"
- `departement` (String 50) : "Commercial", "Consulting" ou "RH"
- `satisfaction_employee_*` (Integer) : scores de 1 à 4
- `augementation_salaire_precedente` (String 10) : format pourcentage ("15 %")
- `a_quitte_l_entreprise` (String 10) : variable cible ("Oui" / "Non")

#### `predictions` - Log temps réel des appels API

Chaque appel à `POST /api/v1/predict` insère une ligne dans cette table.

| Colonne | Type | Rôle |
|---------|------|------|
| `id` | Integer (PK) | Identifiant auto-incrémenté |
| `input_data` | JSON | Données d'entrée complètes (27 champs) envoyées par le client |
| `prediction` | Integer | Résultat du modèle : 0 (Reste) ou 1 (Quitte) |
| `probability` | Float | Probabilité de la classe positive [0, 1] |
| `model_version` | String 50 | Version du modèle (défaut "1.0.0") |
| `api_key_used` | String 255 | Hash bcrypt de la clé API ayant effectué l'appel |
| `created_at` | DateTime | Timestamp UTC de la prédiction |

#### `api_keys` - Authentification

| Colonne | Type | Rôle |
|---------|------|------|
| `id` | Integer (PK) | Identifiant auto-incrémenté |
| `key_hash` | String 255 (UNIQUE) | Hash bcrypt de la clé API (jamais la clé en clair) |
| `name` | String 100 | Nom descriptif de la clé (ex: "init_key") |
| `is_active` | Boolean | Si `False`, la clé est rejetée lors de l'authentification |
| `created_at` | DateTime | Timestamp UTC de création |

---

## 2. Système d'authentification

### Choix technique : API Key + bcrypt

Le système repose sur une authentification par **clé API** transmise dans le header HTTP `X-API-Key`, avec stockage du hash **bcrypt** en base de données.

**Pourquoi API Key et pas OAuth2/JWT ?**

Le projet est un POC interne pour Futurisys. Il n'y a pas de notion de sessions utilisateur, pas de scopes d'autorisation, pas de token à durée limitée. Une clé API unique par consommateur couvre le besoin : identifier l'appelant et contrôler l'accès. OAuth2 ajouterait une complexité (serveur d'autorisation, flux d'obtention de token, refresh) qui n'est pas justifiée pour un premier déploiement avec un nombre restreint de consommateurs.

**Pourquoi bcrypt et pas SHA-256 ?**

bcrypt intègre trois propriétés qui le rendent supérieur à SHA-256 pour le hachage de secrets :

1. **Salt aléatoire intégré** : chaque appel à `bcrypt.hashpw()` produit un hash différent pour la même entrée, ce qui rend les rainbow tables inutilisables.
2. **Coût de calcul adaptatif** (work factor) : bcrypt est volontairement lent, ce qui freine les attaques par force brute. Le coût peut être augmenté au fil du temps pour suivre l'évolution du matériel.
3. **Pas de recherche directe en base** : `WHERE key_hash = hash(input)` est impossible car deux hachages de la même clé donnent des résultats différents. Cela oblige à itérer sur les clés actives (voir ci-dessous).

SHA-256 sans salt serait vulnérable aux rainbow tables. SHA-256 avec salt nécessiterait de gérer le salt séparément, sans bénéficier du coût adaptatif.

### Flux d'authentification (`app/middleware/auth.py`)

```
Client                          API (auth.py)                    Base de données
  |                                |                                |
  |-- Header X-API-Key: "abc..." ->|                                |
  |                                |-- SELECT * FROM api_keys    -->|
  |                                |   WHERE is_active = true       |
  |                                |<-- [hash_1, hash_2, ...]    --|
  |                                |                                |
  |                                |-- bcrypt.checkpw("abc", hash_1)|
  |                                |   -> False                     |
  |                                |-- bcrypt.checkpw("abc", hash_2)|
  |                                |   -> True ! (match)            |
  |                                |                                |
  |<-- 201 Created + hash loggé --|                                |
```

En cas de non-match sur toutes les clés : HTTP 401 Unauthorized.

### Pourquoi itérer sur toutes les clés ?

bcrypt produit un hash **unique à chaque appel** grâce au salt aléatoire. Pour une même clé brute `"abc123"`, deux appels à `bcrypt.hashpw()` donnent :

```
$2b$12$eImiTXuWVxfM37uY4JANjQ...  (premier appel)
$2b$12$KxBa9Dc87VQK0mXd2dN5Xu...  (second appel)
```

Il est donc impossible de faire `SELECT * FROM api_keys WHERE key_hash = bcrypt.hash("abc123")`. La seule méthode est de charger tous les hashs actifs et de tester chacun avec `bcrypt.checkpw()`. Pour un POC avec quelques clés, cette approche est performante. En production à grande échelle, on pourrait utiliser un préfixe non hashé de la clé pour pré-filtrer.

### Cycle de vie des clés

| Étape | Mécanisme | Référence code |
|-------|-----------|---------------|
| **Génération** | `secrets.token_urlsafe(32)` ou variable `INIT_API_KEY` | `scripts/init_db.py` |
| **Hachage** | `bcrypt.hashpw(clé.encode(), bcrypt.gensalt())` | `app/middleware/auth.py:hash_api_key()` |
| **Stockage** | INSERT dans `api_keys` (hash uniquement, jamais la clé brute) | `scripts/init_db.py:creer_api_key()` |
| **Vérification** | `bcrypt.checkpw(clé_reçue, hash_stocké)` sur chaque hash actif | `app/middleware/auth.py:verify_raw_key()` |
| **Désactivation** | `UPDATE api_keys SET is_active = False` | Manuel (pas d'endpoint dédié dans le POC) |
| **Audit** | Hash loggé dans `predictions.api_key_used` à chaque prédiction | `app/services/db_service.py:log_prediction()` |

---

## 3. Architecture dual-engine (SQLite / PostgreSQL)

### Principe

L'application supporte deux moteurs de base de données, sélectionnés **uniquement** via la variable d'environnement `DATABASE_URL`. Le code applicatif (ORM, requêtes, sessions) est identique quel que soit le moteur.

### Configuration (`app/models/database.py`)

```python
from app.config import settings

# Détection automatique du moteur
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
```

Le paramètre `check_same_thread=False` est nécessaire pour SQLite car FastAPI est asynchrone (plusieurs threads accèdent à la même connexion). PostgreSQL n'a pas cette limitation.

### Environnements

| Environnement | Moteur | `DATABASE_URL` | Justification |
|---|---|---|---|
| **Dev local** | SQLite | `sqlite:///./attrition.db` | Aucune dépendance externe, fichier unique |
| **CI (GitHub Actions)** | SQLite | `sqlite:///./test.db` | Pas besoin d'un service container PostgreSQL, tests rapides |
| **Production (HF Spaces)** | PostgreSQL Neon | `postgresql://user:pwd@ep-xxx.neon.tech/attrition_db` | Concurrence, persistance, performance en production |

### SQLAlchemy 2.0 - Declarative Mapping v2

L'ORM utilise les conventions modernes de SQLAlchemy 2.0 :

- **`Mapped[type]`** au lieu de `Column()` : typage Python natif pour chaque colonne
- **`mapped_column()`** au lieu de `Column()` : API déclarative v2
- **`DeclarativeBase`** au lieu de `declarative_base()` : classe de base moderne
- **`Depends(get_db)`** : injection de dépendances FastAPI pour la session DB (une session par requête, fermée automatiquement)

---

## 4. Initialisation des données (`scripts/init_db.py`)

### Processus de fusion des 3 CSV

```
extrait_sirh.csv          extrait_eval.csv         extrait_sondage.csv
(données RH)              (évaluations)            (satisfaction)
      |                         |                         |
      +---- pd.merge() ---------+                         |
                |                                          |
                +-------------- pd.merge() ----------------+
                                   |
                          Nettoyage des clés de jointure
                                   |
                          1 470 employés fusionnés
                                   |
                          INSERT INTO employees
```

Le script réalise ensuite la création de la première clé API (depuis `INIT_API_KEY` ou générée aléatoirement via `secrets.token_urlsafe(32)`), hashée avec bcrypt avant insertion dans `api_keys`.

### Script SQL alternatif (`scripts/create_db.sql`)

En complément de l'ORM (qui crée les tables via `Base.metadata.create_all()`), un script SQL PostgreSQL est fourni. Il ajoute des contraintes et des index non gérés par l'ORM :

**Contraintes CHECK** :
- `satisfaction_employee_environnement BETWEEN 1 AND 4`
- `satisfaction_employee_nature_travail BETWEEN 1 AND 4`
- `satisfaction_employee_equipe BETWEEN 1 AND 4`
- `satisfaction_employee_equilibre_pro_perso BETWEEN 1 AND 4`

**Index de performance** :
- `idx_predictions_created_at` sur `predictions.created_at` (requêtes temporelles)
- `idx_api_keys_hash` sur `api_keys.key_hash` (lookup d'authentification)
- `idx_employees_departement` sur `employees.departement` (filtrage par département)

---

## 5. Sécurité et conformité

### Bonnes pratiques implémentées

| Mesure | Détail |
|--------|--------|
| **Hachage bcrypt** | Salt aléatoire, coût adaptatif, résistant au brute-force |
| **Pas de stockage en clair** | La clé brute n'est jamais persistée en base ni dans les logs |
| **`.env` exclu du dépôt** | `.gitignore` contient explicitement `.env` |
| **Secrets CI/CD** | GitHub Secrets pour `HF_TOKEN`, `PROD_DATABASE_URL`, `INIT_API_KEY` |
| **Secrets production** | Injectés via `HfApi.add_space_secret()` dans le workflow `deploy.yml` |
| **Protection injection SQL** | SQLAlchemy ORM avec requêtes paramétrées (aucune requête SQL brute dans le code applicatif) |
| **Validation des entrées** | Pydantic v2 avec `Field(ge=, le=)`, `Literal[]`, `pattern=` (regex) comme première couche de défense |

### Données personnelles (RGPD)

Le dataset contient des données RH (âge, genre, salaire, département, satisfaction) qui, dans un contexte réel, constitueraient des données personnelles au sens du RGPD (article 4).

Mesures en place dans le POC :
- Accès aux données protégé par authentification API Key + bcrypt
- Pas de données nominatives dans le dataset (identifiants numériques auto-incrémentés)
- Logs d'accès par clé API (colonne `api_key_used` dans `predictions`)
- Hachage des identifiants d'accès (clés API jamais stockées en clair)
- Secrets de connexion non commités dans le dépôt Git

En production, il faudrait ajouter : un registre de traitements (article 30), une analyse d'impact (DPIA, article 35) si traitement à grande échelle, et une politique de rétention des données.

---

## 6. Opérations CRUD (`app/services/db_service.py`)

| Opération | Fonction | Description |
|-----------|----------|-------------|
| **CREATE** | `log_prediction(db, input_data, prediction, probability, api_key_hash)` | Insère une prédiction avec les données d'entrée (JSON), le résultat, la probabilité et le hash de la clé API |
| **READ (liste)** | `get_predictions(db, skip, limit)` | Retourne l'historique paginé des prédictions (défaut : skip=0, limit=100) |
| **READ (unitaire)** | `get_prediction_by_id(db, prediction_id)` | Retourne une prédiction par son ID, ou `None` si inexistante (-> HTTP 404) |
| **READ (auth)** | `get_api_key_by_hash(db, key_hash)` | Retourne la clé API active correspondant au hash (utilisé par le middleware d'authentification) |

Il n'y a pas d'opérations UPDATE ou DELETE exposées par l'API. C'est un choix de conception : les prédictions sont un log d'audit immuable, et la désactivation de clés API se fait directement en base.

---

## 7. Tests de la base de données

### Couverture des modules liés à la base de données

| Module | Statements | Missing | Couverture |
|--------|-----------|---------|-----------|
| `app/models/database.py` | 12 | 0 | 100% |
| `app/models/orm.py` | 52 | 0 | 100% |
| `app/services/db_service.py` | 14 | 0 | 100% |
| `app/middleware/auth.py` | 15 | 0 | 100% |
| **Total** | **93** | **0** | **100%** |

### Tests de la couche données (`test_db.py` - 9 tests)

| Test | Ce qu'il vérifie |
|------|-----------------|
| `test_log_prediction` | Insertion d'une prédiction et vérification de tous les champs |
| `test_log_prediction_preserves_json` | Intégrité du JSON (round-trip : les données insérées sont récupérées identiques) |
| `test_get_predictions_empty` | Requête SELECT sur table vide retourne une liste vide |
| `test_get_predictions_with_data` | Requête SELECT après insertion retourne les données |
| `test_get_prediction_not_found` | ID inexistant retourne `None` |
| `test_get_predictions_pagination` | Les paramètres `skip` et `limit` fonctionnent correctement |
| `test_get_api_key_by_hash_found` | Récupération d'une clé active par son hash |
| `test_get_api_key_by_hash_not_found` | Hash inexistant retourne `None` |
| `test_get_db_yields_session` | Le générateur `get_db()` produit une session SQLAlchemy valide |

### Tests d'authentification (`test_auth.py` - 6 tests)

| Test | Ce qu'il vérifie |
|------|-----------------|
| `test_no_api_key` | Requête sans header `X-API-Key` -> HTTP 422 |
| `test_invalid_api_key` | Clé invalide -> HTTP 401 |
| `test_valid_api_key` | Clé valide -> HTTP 201 (prédiction créée) |
| `test_health_no_auth_required` | `/health` accessible sans authentification |
| `test_hash_api_key_produces_valid_hash` | `bcrypt.hashpw()` produit un hash vérifiable par `bcrypt.checkpw()` |
| `test_hash_api_key_rejects_wrong_key` | Mauvaise clé rejetée par `bcrypt.checkpw()` |

### Stratégie d'isolation

- **Base dédiée** : SQLite `test.db` avec `create_all()` / `drop_all()` par session de test (chaque test part d'un état propre)
- **DI Override** : `app.dependency_overrides[get_db]` injecte la session de test au lieu de la session de production
- **Fixtures pytest** (`conftest.py`) : `setup_test_db` (autouse, crée/détruit les tables), `db_session` (session brute), `client` (TestClient FastAPI), `api_headers` (headers avec clé valide), `valid_employee_data` (données de test complètes)
