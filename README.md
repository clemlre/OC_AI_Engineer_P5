---
title: P5 Attrition API
emoji: "\U0001F4CA"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# API de Prédiction d'Attrition des Employés

API de prédiction d'attrition des employés, développée avec FastAPI. Utilise un modèle Random Forest entraîné sur des données RH, d'évaluation et de sondage pour prédire si un employé va quitter l'entreprise.

**Projet P5 - OpenClassrooms - AI Engineer** | Clément Loire

## Table des matières

- [Contexte métier](#contexte-métier)
- [Architecture](#architecture)
- [Installation](#installation)
- [Utilisation de l'API](#utilisation-de-lapi)
- [Authentification et sécurité](#authentification-et-sécurité)
- [Base de données](#base-de-données)
- [Tests](#tests)
- [Déploiement](#déploiement)
- [Modèle ML](#modèle-ml)
- [CI/CD](#cicd)

## Contexte métier

Futurisys, entreprise innovante, souhaite rendre son modèle de prédiction d'attrition opérationnel et accessible via une API performante. Ce POC permet de :

- **Prédire** si un employé risque de quitter l'entreprise
- **Tracer** toutes les prédictions via une base de données (SQLite en dev, PostgreSQL Neon en prod)
- **Sécuriser** l'accès via un système d'authentification par clé API

## Architecture

```
Client (curl/Postman/App)
    |
    v
[X-API-Key Header] --> Vérification bcrypt
    |
    v
FastAPI (app/main.py)
    |
    +-- GET /health          --> État API + modèle + DB
    +-- POST /api/v1/predict --> Prédiction + log en DB
    +-- GET /api/v1/predictions --> Historique prédictions
    +-- GET /api/v1/predictions/{id} --> Détail prédiction
    |
    v
ML Service (app/services/ml_service.py)
    |-- prepare_input() : feature engineering (4 transformations)
    |-- predict()       : pipeline.predict() + predict_proba()
    |
    v
SQLite (dev/CI) / PostgreSQL Neon (prod)
    |-- employees    : dataset RH complet (1 470 lignes)
    |-- predictions  : log des appels API
    |-- api_keys     : clés d'accès hashées (bcrypt)
```

### Structure du projet

```
api/
+-- app/
|   +-- main.py              # Application FastAPI + lifespan
|   +-- config.py             # Configuration (pydantic-settings)
|   +-- models/
|   |   +-- schemas.py        # Schémas Pydantic v2 (validation 27 champs)
|   |   +-- database.py       # SQLAlchemy 2.0 engine + session
|   |   +-- orm.py            # Modèles ORM (3 tables, Mapped[type])
|   +-- routers/
|   |   +-- health.py         # GET /health
|   |   +-- predictions.py    # Endpoints prédictions
|   +-- services/
|   |   +-- ml_service.py     # Chargement modèle + feature engineering + prédiction
|   |   +-- db_service.py     # Opérations DB (CRUD)
|   +-- middleware/
|       +-- auth.py           # Authentification API Key (bcrypt)
+-- ml_models/
|   +-- best_rf_model.joblib  # Modèle Random Forest (imblearn Pipeline)
+-- data/                     # CSV bruts (SIRH, Eval, Sondage)
+-- scripts/
|   +-- init_db.py            # Initialisation DB + fusion CSV + seed API key
|   +-- create_db.sql         # Script SQL alternatif (PostgreSQL, CHECK, INDEX)
+-- tests/                    # 54 tests Pytest (100% couverture)
+-- .github/workflows/        # CI/CD GitHub Actions (ci.yml + deploy.yml)
+-- Dockerfile                # Conteneur Docker (python:3.11-slim + uv)
+-- docker-compose.yml        # Environnement local (SQLite)
+-- README_BDD.md             # Documentation détaillée de la base de données
```

## Installation

### Prérequis

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (gestionnaire de paquets)

### Installation locale

```bash
# 1. Cloner le dépôt
git clone https://github.com/clemlre/OC_AI_Engineer_P5.git
cd api

# 2. Installer les dépendances
uv sync --group dev

# 3. Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos paramètres (DATABASE_URL, etc.)

# 4. Initialiser la base de données
uv run python scripts/init_db.py
# Note : la clé API générée s'affiche dans le terminal, conservez-la !

# 5. Lancer le serveur
uv run uvicorn app.main:app --reload --port 8567
```

### Installation avec Docker

```bash
# Lancer l'API (SQLite par défaut)
docker-compose up --build

# L'API est accessible sur http://localhost:8567
# La documentation Swagger sur http://localhost:8567/docs
```

## Utilisation de l'API

### Documentation interactive

Une fois le serveur lancé, accédez à :
- **Swagger UI** : `http://localhost:8567/docs`
- **ReDoc** : `http://localhost:8567/redoc`

### Exemples d'appels

#### Vérifier l'état de l'API

```bash
curl http://localhost:8567/health
```

Réponse :
```json
{
  "status": "ok",
  "model_loaded": true,
  "db_connected": true,
  "environment": "dev"
}
```

#### Effectuer une prédiction

```bash
curl -X POST http://localhost:8567/api/v1/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: VOTRE_CLE_API" \
  -d '{
    "age": 35,
    "genre": "M",
    "revenu_mensuel": 6500,
    "statut_marital": "Marie(e)",
    "departement": "Consulting",
    "poste": "Consultant",
    "nombre_experiences_precedentes": 3,
    "annee_experience_totale": 12,
    "annees_dans_l_entreprise": 5,
    "annees_dans_le_poste_actuel": 3,
    "satisfaction_employee_environnement": 3,
    "note_evaluation_precedente": 3,
    "niveau_hierarchique_poste": 2,
    "satisfaction_employee_nature_travail": 3,
    "satisfaction_employee_equipe": 4,
    "satisfaction_employee_equilibre_pro_perso": 3,
    "note_evaluation_actuelle": 3,
    "heure_supplementaires": "Non",
    "augementation_salaire_precedente": "15 %",
    "nombre_participation_pee": 1,
    "nb_formations_suivies": 3,
    "distance_domicile_travail": 10,
    "niveau_education": 3,
    "domaine_etude": "Infra & Cloud",
    "frequence_deplacement": "Occasionnel",
    "annees_depuis_la_derniere_promotion": 1,
    "annes_sous_responsable_actuel": 3
  }'
```

Réponse :
```json
{
  "prediction_id": 1,
  "prediction": 0,
  "probability": 0.1523,
  "label": "Reste",
  "timestamp": "2026-03-27T10:30:00"
}
```

#### Consulter l'historique des prédictions

```bash
curl http://localhost:8567/api/v1/predictions \
  -H "X-API-Key: VOTRE_CLE_API"
```

#### Consulter le détail d'une prédiction

```bash
curl http://localhost:8567/api/v1/predictions/1 \
  -H "X-API-Key: VOTRE_CLE_API"
```

## Authentification et sécurité

### Choix du système d'authentification

L'API utilise un système d'**authentification par clé API** via le header HTTP `X-API-Key`, associé à un hachage **bcrypt** en base de données.

Ce choix est motivé par le contexte du projet (POC interne pour Futurisys) :

- **Clé API plutôt qu'OAuth2/JWT** : le POC n'a pas de notion de sessions utilisateur ni de scopes d'autorisation. Une clé API unique par consommateur est suffisante et plus simple à intégrer pour un premier déploiement. OAuth2 serait pertinent si l'API devait gérer plusieurs niveaux d'accès ou des tokens à durée limitée.
- **bcrypt plutôt que SHA-256** : bcrypt intègre un salt aléatoire et un coût de calcul adaptatif (work factor), ce qui le rend résistant aux attaques par dictionnaire et par force brute. Un hash SHA-256 serait vulnérable aux rainbow tables sans salt explicite. De plus, bcrypt empêche toute recherche directe en base (`WHERE hash = ?`) car deux hachages de la même clé produisent des résultats différents.
- **Itération sur toutes les clés actives** : la vérification parcourt les clés actives avec `bcrypt.checkpw()` une par une. C'est acceptable pour un POC avec peu de clés. En production à grande échelle, une architecture avec un préfixe de clé en clair (pour filtrer) + hash bcrypt du reste serait plus performante.

### Flux d'authentification

1. Le client envoie sa clé brute dans le header `X-API-Key`
2. Le middleware `auth.py` charge tous les hashs actifs depuis la table `api_keys`
3. Pour chaque hash, `bcrypt.checkpw(clé_brute, hash)` est appelé
4. Si un match est trouvé, la requête est autorisée et le hash est loggé dans `predictions.api_key_used`
5. Si aucun match, HTTP 401 Unauthorized

### Bonnes pratiques de sécurité

| Mesure | Implémentation |
|--------|---------------|
| **Hachage des clés** | bcrypt 4.0+ avec salt aléatoire automatique |
| **Validation des entrées** | Pydantic v2 avec contraintes de type, bornes (`Field(ge=, le=)`) et enums (`Literal`) |
| **Protection injection SQL** | SQLAlchemy ORM avec requêtes paramétrées (aucun SQL brut) |
| **Gestion des secrets** | Variables d'environnement (`.env` exclu par `.gitignore`), GitHub Secrets pour CI/CD, `HfApi.add_space_secret()` pour la prod |
| **CORS** | Middleware FastAPI configurable (`allow_origins`) |
| **HTTPS** | Géré par la plateforme Hugging Face Spaces en production |

### Gestion des accès

- Chaque appel API est tracé avec le hash de la clé utilisée (colonne `api_key_used`)
- Les clés inactives sont automatiquement rejetées (HTTP 401)
- Le endpoint `/health` est public (pas d'authentification requise)
- Les clés sont générées via `secrets.token_urlsafe(32)` ou fournies par la variable `INIT_API_KEY`

### Données personnelles

Le dataset contient des données RH (âge, genre, salaire, département) qui, dans un contexte réel, constitueraient des données personnelles au sens du RGPD. Les mesures de protection mises en place (authentification, hachage, absence de données nominatives, logs d'accès) constituent un socle minimal de sécurité. En production, un registre de traitements et une analyse d'impact (DPIA) seraient à prévoir.

## Base de données

> Documentation détaillée : voir [`README_BDD.md`](README_BDD.md)

### Schéma (3 tables)

```
+------------------+     +------------------+     +------------------+
|    employees     |     |   predictions    |     |    api_keys      |
+------------------+     +------------------+     +------------------+
| id (PK)          |     | id (PK)          |     | id (PK)          |
| age              |     | input_data (JSON)|     | key_hash (unique)|
| genre            |     | prediction       |     | name             |
| revenu_mensuel   |     | probability      |     | is_active        |
| statut_marital   |     | model_version    |     | created_at       |
| departement      |     | api_key_used     |     +------------------+
| poste            |     | created_at       |
| ... (28 cols)    |     +------------------+
| a_quitte_l_ent.  |
| created_at       |
+------------------+
```

### Architecture dual-engine

Le code applicatif est **100% agnostique du moteur** grâce à SQLAlchemy 2.0. Seule la variable `DATABASE_URL` change entre les environnements :

| Environnement | Moteur | Configuration |
|---|---|---|
| **Dev / Docker** | SQLite | `sqlite:///./attrition.db` (fichier local) |
| **CI (GitHub Actions)** | SQLite | `sqlite:///./test.db` (éphémère) |
| **Prod (HF Spaces)** | PostgreSQL Neon | URL injectée via `HfApi.add_space_secret()` |

### Processus de stockage

1. **Initialisation** : le script `init_db.py` charge les 3 CSV bruts (SIRH, Évaluation, Sondage), les fusionne via `pd.merge()` et insère les 1 470 employés dans la table `employees`
2. **Prédictions** : chaque appel `POST /predict` enregistre automatiquement les données d'entrée (JSON) et la sortie du modèle dans la table `predictions`
3. **Traçabilité** : la clé API utilisée (hashée) et le timestamp UTC sont enregistrés pour chaque prédiction

## Tests

### Lancer les tests

```bash
# Tests avec rapport de couverture
uv run pytest -v

# Tests avec rapport HTML
uv run pytest --cov=app --cov-report=html
# Rapport disponible dans htmlcov/index.html
```

### Couverture (54 tests, 240 statements, 100%)

| Module | Statements | Missing | Couverture |
|--------|-----------|---------|-----------|
| `app/config.py` | 10 | 0 | 100% |
| `app/main.py` | 16 | 0 | 100% |
| `app/middleware/auth.py` | 15 | 0 | 100% |
| `app/models/database.py` | 12 | 0 | 100% |
| `app/models/orm.py` | 52 | 0 | 100% |
| `app/models/schemas.py` | 45 | 0 | 100% |
| `app/routers/health.py` | 22 | 0 | 100% |
| `app/routers/predictions.py` | 22 | 0 | 100% |
| `app/services/db_service.py` | 14 | 0 | 100% |
| `app/services/ml_service.py` | 32 | 0 | 100% |
| **TOTAL** | **240** | **0** | **100%** |

### Répartition des 54 tests par module

| Fichier | Tests | Périmètre |
|---------|-------|-----------|
| `test_schemas.py` | 15 | Validation Pydantic : typage, bornes, enums, regex, champs requis |
| `test_ml_service.py` | 11 | Feature engineering : nettoyage %, mapping ordinal, 3 ratios, singleton modèle |
| `test_predictions.py` | 10 | Endpoints REST : prédiction valide, champ manquant, catégorie invalide, hors bornes, pagination, 404 |
| `test_db.py` | 9 | Opérations CRUD : insert, select, pagination, préservation JSON, clé API par hash |
| `test_auth.py` | 6 | Authentification : sans clé (422), clé invalide (401), clé valide, /health sans auth, hachage bcrypt |
| `test_health.py` | 3 | Health check : nominal, modèle non chargé, base de données indisponible |

### Stratégie d'isolation des tests

- **Base de données dédiée** : SQLite `test.db` avec `create_all()` / `drop_all()` par session de test (chaque test part d'un état propre)
- **Injection de dépendances (DI Override)** : `app.dependency_overrides[get_db]` remplace la session de production par la session de test
- **Mock du modèle ML** : `MagicMock` avec `predict=[1]` et `predict_proba=[[0.15, 0.85]]` pour isoler les tests API du modèle réel (pas de dépendance au fichier `.joblib`)

### Scénarios d'erreur testés

- Requête sans header `X-API-Key` (HTTP 422)
- Clé API invalide (HTTP 401)
- Champ requis manquant dans le body (HTTP 422)
- Valeur catégorielle invalide (HTTP 422)
- Valeur numérique hors bornes (HTTP 422)
- Body vide (HTTP 422)
- Prédiction inexistante par ID (HTTP 404)
- Base de données indisponible (health check `db_connected: false`)
- Modèle ML non chargé (health check `model_loaded: false`)

## Déploiement

### Hugging Face Spaces

Le déploiement sur HF Spaces est automatisé via GitHub Actions :

1. Créer un Space Docker sur [huggingface.co/spaces](https://huggingface.co/spaces)
2. Configurer les secrets GitHub : `HF_TOKEN`, `PROD_DATABASE_URL`, `INIT_API_KEY`
3. Pousser un tag : `git tag v1.0.x && git push --tags`
4. Le workflow `deploy.yml` injecte les secrets sur HF Spaces via `HfApi.add_space_secret()` puis uploade le code via `HfApi.upload_folder()`

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL de connexion SQLite ou PostgreSQL | `sqlite:///./attrition.db` |
| `MODEL_PATH` | Chemin vers le modèle joblib | `ml_models/best_rf_model.joblib` |
| `ENVIRONMENT` | Environnement (`dev` ou `prod`) | `prod` |
| `INIT_API_KEY` | Clé API initiale (utilisée par `init_db.py`) | Générée aléatoirement si absente |

## Modèle ML

### Description

- **Algorithme** : Random Forest Classifier (scikit-learn + imblearn)
- **Objectif** : prédire si un employé va quitter l'entreprise (`a_quitte_l_entreprise`)
- **Pipeline** : ColumnTransformer (StandardScaler + OrdinalEncoder + OneHotEncoder) -> SMOTE -> RandomForest

### Performance (jeu de test)

| Métrique | Valeur |
|----------|--------|
| Accuracy | ~82% |
| Precision (classe positive) | ~43% |
| Recall (classe positive) | ~40% |
| F1-Score (classe positive) | ~0.42 |

### Features d'entrée (27 champs bruts -> 30 features)

Le modèle attend 27 champs bruts issus de 3 sources de données (SIRH, Évaluation, Sondage). Le service ML (`ml_service.py`) applique 4 transformations avant l'inférence :

1. **Nettoyage** : conversion des pourcentages (`"15 %"` -> `15.0`)
2. **Mapping ordinal** : encodage des fréquences (`"Aucun"` -> 0, `"Occasionnel"` -> 1, `"Fréquent"` -> 2)
3. **Feature engineering** : calcul de 3 ratios (`ratio_ancienneté_age`, `ratio_stabilité_poste`, `revenu_par_année_age`)
4. **Ordonnancement** : réarrangement des colonnes selon `FEATURE_ORDER` (30 colonnes dans l'ordre exact attendu par le pipeline)

### Sérialisation

Le modèle est sauvegardé au format **joblib** (recommandé par scikit-learn) et chargé en **singleton** (une seule fois au démarrage via `get_model()`).

## CI/CD

### Pipeline d'intégration continue (`ci.yml`)

Déclenché sur : push vers `main`/`develop`, pull requests vers `main`

1. **Lint** : vérification du code avec `ruff check app/ tests/`
2. **Tests** : exécution de `pytest` avec SQLite éphémère (`DATABASE_URL=sqlite:///./test.db`)
3. **Couverture** : rapport XML uploadé en artifact GitHub

### Pipeline de déploiement (`deploy.yml`)

Déclenché sur : push de tag `v*`

1. Injection des secrets sur HF Spaces (`DATABASE_URL`, `INIT_API_KEY`, `ENVIRONMENT`) via `HfApi.add_space_secret()`
2. Upload du code vers HF Spaces via `HfApi.upload_folder()` (contourne la limitation git push avec LFS)

### Gestion des environnements

| Environnement | Base de données | Déclencheur |
|--------------|-----------------|-------------|
| **dev** | SQLite locale (`attrition.db`) | `uv run uvicorn` |
| **CI** | SQLite éphémère (`test.db`) | push main/develop, PR main |
| **prod** | PostgreSQL Neon (cloud) | Tag `v*` -> deploy.yml |

### Secrets

Les secrets sont gérés via :
- **Localement** : fichier `.env` (non commité, exclu par `.gitignore`)
- **CI/CD** : GitHub Secrets (`HF_TOKEN`, `PROD_DATABASE_URL`, `INIT_API_KEY`)
- **Production** : injection via `HfApi.add_space_secret()` dans le workflow de déploiement
