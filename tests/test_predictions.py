"""Tests fonctionnels pour les endpoints de prédiction."""

import pytest


class TestPredictEndpoint:
    """Tests du endpoint POST /api/v1/predict."""

    def test_predict_valid_data(self, client, api_headers, valid_employee_data):
        """Une prédiction avec des données valides retourne 201."""
        response = client.post(
            "/api/v1/predict", json=valid_employee_data, headers=api_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert "prediction_id" in data
        assert data["prediction"] in [0, 1]
        assert 0.0 <= data["probability"] <= 1.0
        assert data["label"] in ["Reste", "Quitte"]
        assert "timestamp" in data

    def test_predict_missing_field(self, client, api_headers, valid_employee_data):
        """Des données incomplètes retournent 422."""
        del valid_employee_data["age"]
        response = client.post(
            "/api/v1/predict", json=valid_employee_data, headers=api_headers
        )
        assert response.status_code == 422

    def test_predict_invalid_categorical(self, client, api_headers, valid_employee_data):
        """Une valeur catégorielle invalide retourne 422."""
        valid_employee_data["departement"] = "Finance"
        response = client.post(
            "/api/v1/predict", json=valid_employee_data, headers=api_headers
        )
        assert response.status_code == 422

    def test_predict_out_of_range(self, client, api_headers, valid_employee_data):
        """Une valeur hors bornes retourne 422."""
        valid_employee_data["age"] = 10
        response = client.post(
            "/api/v1/predict", json=valid_employee_data, headers=api_headers
        )
        assert response.status_code == 422

    def test_predict_empty_body(self, client, api_headers):
        """Un body vide retourne 422."""
        response = client.post("/api/v1/predict", json={}, headers=api_headers)
        assert response.status_code == 422


class TestListPredictions:
    """Tests du endpoint GET /api/v1/predictions."""

    def test_list_predictions_empty(self, client, api_headers):
        """La liste de prédictions vide retourne un array vide."""
        response = client.get("/api/v1/predictions", headers=api_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_predictions_after_predict(self, client, api_headers, valid_employee_data):
        """Après une prédiction, la liste contient un élément."""
        client.post("/api/v1/predict", json=valid_employee_data, headers=api_headers)
        response = client.get("/api/v1/predictions", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_predictions_pagination(self, client, api_headers, valid_employee_data):
        """La pagination fonctionne correctement."""
        # Créer 3 prédictions
        for _ in range(3):
            client.post("/api/v1/predict", json=valid_employee_data, headers=api_headers)

        response = client.get("/api/v1/predictions?limit=2", headers=api_headers)
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestGetPrediction:
    """Tests du endpoint GET /api/v1/predictions/{id}."""

    def test_get_prediction_exists(self, client, api_headers, valid_employee_data):
        """Récupérer une prédiction existante retourne 200."""
        create_resp = client.post(
            "/api/v1/predict", json=valid_employee_data, headers=api_headers
        )
        pred_id = create_resp.json()["prediction_id"]

        response = client.get(f"/api/v1/predictions/{pred_id}", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["prediction_id"] == pred_id
        assert "input_data" in data

    def test_get_prediction_not_found(self, client, api_headers):
        """Une prédiction inexistante retourne 404."""
        response = client.get("/api/v1/predictions/99999", headers=api_headers)
        assert response.status_code == 404
