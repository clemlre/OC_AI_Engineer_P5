"""Tests unitaires pour les opérations en base de données."""

import bcrypt as _bcrypt
from sqlalchemy import text

from app.models.database import get_db
from app.models.orm import ApiKey, Prediction
from app.services.db_service import (
    get_api_key_by_hash,
    get_prediction_by_id,
    get_predictions,
    log_prediction,
)


class TestLogPrediction:
    """Tests de l'enregistrement des prédictions."""

    def test_log_prediction(self, db_session):
        """Une prédiction loggée est correctement enregistrée."""
        input_data = {"age": 35, "genre": "M", "departement": "Consulting"}

        pred = log_prediction(
            db=db_session,
            input_data=input_data,
            prediction=1,
            probability=0.85,
            api_key_used="hash_test",
        )

        assert pred.id is not None
        assert pred.prediction == 1
        assert pred.probability == 0.85
        assert pred.input_data == input_data
        assert pred.api_key_used == "hash_test"

    def test_log_prediction_preserves_json(self, db_session):
        """Les données JSONB sont fidèlement préservées."""
        input_data = {
            "age": 25,
            "genre": "F",
            "statut_marital": "Célibataire",
            "augementation_salaire_precedente": "11 %",
        }

        pred = log_prediction(
            db=db_session,
            input_data=input_data,
            prediction=0,
            probability=0.12,
            api_key_used="hash_test",
        )

        retrieved = get_prediction_by_id(db_session, pred.id)
        assert retrieved.input_data["statut_marital"] == "Célibataire"
        assert retrieved.input_data["augementation_salaire_precedente"] == "11 %"


class TestGetPredictions:
    """Tests de récupération des prédictions."""

    def test_get_predictions_empty(self, db_session):
        """Une base vide retourne une liste vide."""
        result = get_predictions(db_session)
        assert result == []

    def test_get_predictions_with_data(self, db_session):
        """Les prédictions insérées sont retournées."""
        for i in range(3):
            log_prediction(
                db=db_session,
                input_data={"index": i},
                prediction=i % 2,
                probability=0.5,
                api_key_used="hash",
            )

        result = get_predictions(db_session)
        assert len(result) == 3

    def test_get_prediction_not_found(self, db_session):
        """Un ID inexistant retourne None."""
        result = get_prediction_by_id(db_session, 99999)
        assert result is None

    def test_get_predictions_pagination(self, db_session):
        """La pagination fonctionne correctement."""
        for i in range(5):
            log_prediction(
                db=db_session,
                input_data={"i": i},
                prediction=0,
                probability=0.1,
                api_key_used="h",
            )

        result = get_predictions(db_session, skip=0, limit=2)
        assert len(result) == 2

        result_skip = get_predictions(db_session, skip=3, limit=10)
        assert len(result_skip) == 2


class TestGetApiKey:
    """Tests de récupération des clés API."""

    def test_get_api_key_by_hash_found(self, db_session):
        """Retrouve une clé active par son hash."""
        key_hash = _bcrypt.hashpw(b"test", _bcrypt.gensalt()).decode("utf-8")
        db_session.add(ApiKey(key_hash=key_hash, name="test"))
        db_session.commit()

        result = get_api_key_by_hash(db_session, key_hash)
        assert result is not None
        assert result.name == "test"

    def test_get_api_key_by_hash_not_found(self, db_session):
        """Un hash inexistant retourne None."""
        result = get_api_key_by_hash(db_session, "nonexistent")
        assert result is None


class TestGetDbDependency:
    """Tests du générateur get_db."""

    def test_get_db_yields_session(self):
        """get_db() produit une session fonctionnelle puis la ferme."""
        gen = get_db()
        session = next(gen)
        assert session is not None
        # Vérifier que la session est utilisable
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        # Fermer proprement
        try:
            next(gen)
        except StopIteration:
            pass
