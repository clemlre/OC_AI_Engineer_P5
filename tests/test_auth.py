"""Tests fonctionnels pour l'authentification API."""

from app.middleware.auth import hash_api_key, verify_raw_key


class TestAuthentication:
    """Tests de la vérification de clé API."""

    def test_no_api_key(self, client, valid_employee_data):
        """Une requête sans clé API retourne 422 (header manquant)."""
        response = client.post("/api/v1/predict", json=valid_employee_data)
        assert response.status_code == 422

    def test_invalid_api_key(self, client, valid_employee_data):
        """Une clé API invalide retourne 401."""
        response = client.post(
            "/api/v1/predict",
            json=valid_employee_data,
            headers={"X-API-Key": "invalid-key-12345"},
        )
        assert response.status_code == 401

    def test_valid_api_key(self, client, api_headers, valid_employee_data):
        """Une clé API valide retourne 201."""
        response = client.post(
            "/api/v1/predict", json=valid_employee_data, headers=api_headers
        )
        assert response.status_code == 201

    def test_health_no_auth_required(self, client):
        """Le endpoint /health ne nécessite pas d'authentification."""
        response = client.get("/health")
        assert response.status_code == 200


class TestHashApiKey:
    """Tests des fonctions utilitaires de hachage."""

    def test_hash_api_key_produces_valid_hash(self):
        """hash_api_key produit un hash vérifiable."""
        raw = "my-secret-key"
        hashed = hash_api_key(raw)
        assert verify_raw_key(raw, hashed)

    def test_hash_api_key_rejects_wrong_key(self):
        """Un mauvais mot de passe ne vérifie pas."""
        hashed = hash_api_key("correct-key")
        assert not verify_raw_key("wrong-key", hashed)
