from unittest.mock import MagicMock

import bcrypt as _bcrypt
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.database import Base, get_db
from app.models.orm import ApiKey
from app.services import ml_service

# Base de données de test (SQLite en mémoire)
TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Clé API de test
TEST_API_KEY = "test-api-key-12345"
TEST_API_KEY_HASH = _bcrypt.hashpw(
    TEST_API_KEY.encode("utf-8"), _bcrypt.gensalt()
).decode("utf-8")


@pytest.fixture(autouse=True)
def setup_test_db():
    """Crée et nettoie la base de test pour chaque test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Session DB de test."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def override_get_db():
    """Override la dépendance get_db pour utiliser la DB de test."""
    def _get_test_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
    return _get_test_db


@pytest.fixture
def mock_model():
    """Mock du modèle ML qui retourne toujours prediction=1, proba=0.85."""
    mock = MagicMock()
    mock.predict.return_value = np.array([1])
    mock.predict_proba.return_value = np.array([[0.15, 0.85]])
    return mock


@pytest.fixture
def client(override_get_db, mock_model, db_session):
    """Client de test FastAPI avec DB de test et modèle mocké."""
    # Override DB
    app.dependency_overrides[get_db] = override_get_db

    # Insérer la clé API de test
    api_key = ApiKey(key_hash=TEST_API_KEY_HASH, name="test_key")
    db_session.add(api_key)
    db_session.commit()

    # Mock du modèle
    ml_service._model = mock_model

    with TestClient(app) as c:
        yield c

    # Cleanup
    app.dependency_overrides.clear()
    ml_service._model = None


@pytest.fixture
def api_headers():
    """Headers avec la clé API de test."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def valid_employee_data():
    """Données d'employé valides pour les tests."""
    return {
        "age": 35,
        "genre": "M",
        "revenu_mensuel": 6500,
        "statut_marital": "Marié(e)",
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
        "annes_sous_responsable_actuel": 3,
    }
