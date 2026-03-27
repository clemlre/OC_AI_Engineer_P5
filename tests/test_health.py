"""Tests pour le endpoint /health, incluant les cas dégradés."""

from unittest.mock import patch


from app.main import app
from app.models.database import get_db


class TestHealthEndpoint:
    """Tests du endpoint GET /health."""

    def test_health_ok(self, client):
        """Health check retourne ok quand tout fonctionne."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["model_loaded"] is True
        assert data["db_connected"] is True

    def test_health_model_not_loaded(self, client):
        """Health check retourne degraded quand le modèle n'est pas chargé."""
        with patch("app.routers.health.get_model", side_effect=Exception("no model")):
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["model_loaded"] is False
        assert data["status"] == "degraded"

    def test_health_db_down(self, client):
        """Health check retourne degraded quand la DB est inaccessible."""
        def broken_db():
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            bad_engine = create_engine("sqlite:///./nonexistent_dir/x/y/z.db")
            session = sessionmaker(bind=bad_engine)()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = broken_db
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["db_connected"] is False
        assert data["status"] == "degraded"
