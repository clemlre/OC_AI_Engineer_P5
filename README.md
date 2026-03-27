---
title: P5 Attrition API
emoji: "\U0001F4CA"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# API Prediction Attrition Employes

API de prediction d'attrition des employes, developpee avec FastAPI. Utilise un modele Random Forest entraine sur des donnees RH, d'evaluation et de sondage pour predire si un employe va quitter l'entreprise.

**Projet P5 - OpenClassrooms - Data Scientist** | Clement Loire

## Table des matieres

- [Contexte metier](#contexte-metier)
- [Architecture](#architecture)
- [Installation](#installation)
- [Utilisation de l'API](#utilisation-de-lapi)
- [Authentification et securite](#authentification-et-securite)
- [Base de donnees](#base-de-donnees)
- [Tests](#tests)
- [Deploiement](#deploiement)
- [Modele ML](#modele-ml)
- [CI/CD](#cicd)

## Contexte metier

Futurisys, entreprise innovante, souhaite rendre son modele de prediction d'attrition operationnel et accessible via une API performante. Ce POC permet de :

- **Predire** si un employe risque de quitter l'entreprise
- **Tracer** toutes les predictions via une base de donnees PostgreSQL
- **Securiser** l'acces via un systeme d'authentification par cle API

## Architecture

```
Client (curl/Postman/App)
    |
    v
[X-API-Key Header] --> Verification bcrypt
    |
    v
FastAPI (app/main.py)
    |
    +-- GET /health          --> Etat API + modele + DB
    +-- POST /api/v1/predict --> Prediction + log en DB
    +-- GET /api/v1/predictions --> Historique predictions
    +-- GET /api/v1/predictions/{id} --> Detail prediction
    |
    v
ML Service (app/services/ml_service.py)
    |-- prepare_input() : feature engineering
    |-- predict()       : pipeline.predict() + predict_proba()
    |
    v
PostgreSQL / SQLite
    |-- employees    : dataset complet
    |-- predictions  : log des appels API
    |-- api_keys     : cles d'acces hashees
```

### Structure du projet

```
api/
+-- app/
|   +-- main.py              # Application FastAPI
|   +-- config.py             # Configuration (pydantic-settings)
|   +-- models/
|   |   +-- schemas.py        # Schemas Pydantic (validation)
|   |   +-- database.py       # SQLAlchemy engine + session
|   |   +-- orm.py            # Modeles ORM (tables)
|   +-- routers/
|   |   +-- health.py         # GET /health
|   |   +-- predictions.py    # Endpoints predictions
|   +-- services/
|   |   +-- ml_service.py     # Chargement modele + prediction
|   |   +-- db_service.py     # Operations DB
|   +-- middleware/
|       +-- auth.py           # Authentification API key
+-- ml_models/
|   +-- best_rf_model.joblib  # Modele Random Forest
+-- data/                     # CSV bruts (SIRH, Eval, Sondage)
+-- scripts/
|   +-- init_db.py            # Initialisation DB + dataset
|   +-- create_db.sql         # Script SQL alternatif
+-- tests/                    # Tests Pytest
+-- .github/workflows/        # CI/CD GitHub Actions
+-- Dockerfile                # Conteneur Docker
+-- docker-compose.yml        # PostgreSQL + API
```

## Installation

### Prerequis

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (gestionnaire de paquets)
- PostgreSQL 16+ (ou Docker)

### Installation locale

```bash
# 1. Cloner le depot
git clone https://github.com/<user>/api.git
cd api

# 2. Installer les dependances
uv sync --group dev

# 3. Configurer l'environnement
cp .env.example .env
# Editer .env avec vos parametres (DATABASE_URL, etc.)

# 4. Initialiser la base de donnees
uv run python scripts/init_db.py
# Note : la cle API generee s'affiche dans le terminal, conservez-la !

# 5. Lancer le serveur
uv run uvicorn app.main:app --reload --port 8567
```

### Installation avec Docker

```bash
# Lancer PostgreSQL + API
docker-compose up --build

# L'API est accessible sur http://localhost:8567
# La documentation Swagger sur http://localhost:8567/docs
```

## Utilisation de l'API

### Documentation interactive

Une fois le serveur lance, accedez a :
- **Swagger UI** : `http://localhost:8567/docs`
- **ReDoc** : `http://localhost:8567/redoc`

### Exemples d'appels

#### Verifier l'etat de l'API

```bash
curl http://localhost:8567/health
```

Reponse :
```json
{
  "status": "ok",
  "model_loaded": true,
  "db_connected": true,
  "environment": "dev"
}
```

#### Effectuer une prediction

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

Reponse :
```json
{
  "prediction_id": 1,
  "prediction": 0,
  "probability": 0.1523,
  "label": "Reste",
  "timestamp": "2026-03-27T10:30:00"
}
```

#### Consulter l'historique des predictions

```bash
curl http://localhost:8567/api/v1/predictions \
  -H "X-API-Key: VOTRE_CLE_API"
```

#### Consulter le detail d'une prediction

```bash
curl http://localhost:8567/api/v1/predictions/1 \
  -H "X-API-Key: VOTRE_CLE_API"
```

## Authentification et securite

### Systeme d'authentification

L'API utilise un systeme d'**authentification par cle API** via le header `X-API-Key` :

1. Les cles sont generees lors de l'initialisation (`scripts/init_db.py`)
2. Elles sont stockees **hashees avec bcrypt** dans la table `api_keys`
3. Chaque requete authentifiee est verifiee contre les hashs en base
4. Les cles peuvent etre desactivees (`is_active = false`)

### Bonnes pratiques de securite

| Mesure | Implementation |
|--------|---------------|
| **Hachage des cles** | bcrypt (resistant aux attaques par force brute) |
| **Validation des entrees** | Pydantic avec contraintes de type, bornes et enums |
| **Protection injection SQL** | SQLAlchemy ORM (requetes parametrees) |
| **Gestion des secrets** | Variables d'environnement (`.env`), pas de secrets dans le code |
| **CORS** | Middleware configurable |
| **HTTPS** | Recommande en production (gere par le reverse proxy) |

### Gestion des acces

- Chaque appel API est trace avec le hash de la cle utilisee
- Les cles inactives sont automatiquement rejetees (HTTP 401)
- Le endpoint `/health` est public (pas d'authentification requise)

## Base de donnees

### Schema UML

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

### Processus de stockage et gestion des donnees

1. **Initialisation** : le script `init_db.py` charge les 3 CSV bruts (SIRH, Evaluation, Sondage), les fusionne et insere le dataset complet (1470 employes) dans la table `employees`
2. **Predictions** : chaque appel `POST /predict` enregistre automatiquement les donnees d'entree (JSONB) et la sortie du modele dans la table `predictions`
3. **Tracabilite** : la cle API utilisee (hashee) et le timestamp sont enregistres pour chaque prediction

### Besoins analytiques

La table `predictions` permet de :
- Suivre le volume de predictions dans le temps
- Analyser la distribution des predictions (Reste vs Quitte)
- Auditer les appels par cle API
- Comparer les entrees aux donnees du dataset original (`employees`)

### Compatibilite

- **Local / Docker** : PostgreSQL 16 (via `docker-compose.yml`)
- **Hugging Face Spaces** : SQLite en fallback (meme code SQLAlchemy, seul `DATABASE_URL` change)

## Tests

### Lancer les tests

```bash
# Tests avec rapport de couverture
uv run pytest -v

# Tests avec rapport HTML
uv run pytest --cov=app --cov-report=html
# Rapport disponible dans htmlcov/index.html
```

### Couverture

| Module | Couverture |
|--------|-----------|
| `app/config.py` | 100% |
| `app/main.py` | 100% |
| `app/middleware/auth.py` | 93% |
| `app/models/orm.py` | 100% |
| `app/models/schemas.py` | 100% |
| `app/routers/predictions.py` | 100% |
| `app/services/ml_service.py` | 97% |
| `app/services/db_service.py` | 93% |
| **TOTAL** | **95%** |

### Types de tests

- **Tests unitaires** : validation Pydantic, feature engineering, operations DB
- **Tests fonctionnels** : endpoints API (predict, list, detail), authentification
- **44 tests** couvrant les cas critiques et les scenarios d'erreur

## Deploiement

### Hugging Face Spaces

Le deploiement sur HF Spaces est automatise via GitHub Actions :

1. Creer un Space Docker sur [huggingface.co/spaces](https://huggingface.co/spaces)
2. Configurer les secrets GitHub :
   - `HF_TOKEN` : token d'acces Hugging Face
   - `HF_SPACE_NAME` : `<user>/api`
3. Pousser un tag : `git tag v1.0.0 && git push --tags`
4. Le workflow `deploy.yml` pousse automatiquement vers HF Spaces

### Variables d'environnement

| Variable | Description | Defaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL de connexion PostgreSQL ou SQLite | `sqlite:///./attrition.db` |
| `MODEL_PATH` | Chemin vers le modele joblib | `ml_models/best_rf_model.joblib` |
| `ENVIRONMENT` | Environnement (`dev` ou `prod`) | `dev` |
| `INIT_API_KEY` | Cle API initiale (utilisee par init_db.py) | generee aleatoirement |

## Modele ML

### Description

- **Algorithme** : Random Forest Classifier (scikit-learn + imblearn)
- **Objectif** : predire si un employe va quitter l'entreprise (`a_quitte_l_entreprise`)
- **Pipeline** : ColumnTransformer (StandardScaler + OrdinalEncoder + OneHotEncoder) -> SMOTE -> RandomForest

### Performance (jeu de test)

| Metrique | Valeur |
|----------|--------|
| Accuracy | ~82% |
| Precision (classe positive) | ~43% |
| Recall (classe positive) | ~40% |
| F1-Score (classe positive) | ~0.42 |

### Features d'entree (25 champs bruts + 3 engineeres)

Le modele attend 25 champs bruts issus de 3 sources de donnees (SIRH, Evaluation, Sondage). Le service ML calcule automatiquement 3 features supplementaires :
- `ratio_anciennete_age` = annees_entreprise / age
- `ratio_stabilite_poste` = annees_poste / annees_entreprise
- `revenu_par_annee_age` = revenu_mensuel / age

### Serialisation

Le modele est sauvegarde au format **joblib** (recommande par scikit-learn pour la serialisation d'objets numpy volumineux).

## CI/CD

### Pipeline d'integration continue (`ci.yml`)

Declenche sur : push vers `main`/`develop`, pull requests vers `main`

1. **Lint** : verification du code avec `ruff`
2. **Tests** : execution de pytest avec PostgreSQL (service container)
3. **Couverture** : rapport XML uploade en artifact

### Pipeline de deploiement (`deploy.yml`)

Declenche sur : push de tag `v*`

1. Push automatique vers Hugging Face Spaces

### Gestion des environnements

| Environnement | Base de donnees | Declencheur |
|--------------|-----------------|-------------|
| **dev** | SQLite locale | `uv run uvicorn` |
| **test** | SQLite en memoire / PostgreSQL CI | `uv run pytest` |
| **prod** | PostgreSQL (Docker) ou SQLite (HF) | Tag `v*` |

### Secrets

Les secrets sont geres via :
- **Localement** : fichier `.env` (non commite, dans `.gitignore`)
- **CI/CD** : GitHub Secrets (`HF_TOKEN`, `HF_SPACE_NAME`)
- **Docker** : variables d'environnement dans `docker-compose.yml`
