"""Tests unitaires pour le service ML."""

from unittest.mock import MagicMock, patch

import pytest

from app.models.schemas import EmployeeInput
from app.services import ml_service
from app.services.ml_service import FEATURE_ORDER, prepare_input


class TestPrepareInput:
    """Tests de la fonction prepare_input()."""

    def test_output_has_correct_columns(self, valid_employee_data):
        """Le DataFrame de sortie doit avoir exactement 30 colonnes dans le bon ordre."""
        employee = EmployeeInput(**valid_employee_data)
        df = prepare_input(employee)

        assert list(df.columns) == FEATURE_ORDER
        assert len(df.columns) == 30
        assert len(df) == 1

    def test_augmentation_cleaned(self, valid_employee_data):
        """Le pourcentage d'augmentation doit être converti en float."""
        valid_employee_data["augementation_salaire_precedente"] = "15 %"
        employee = EmployeeInput(**valid_employee_data)
        df = prepare_input(employee)

        assert df["augementation_salaire_precedente"].iloc[0] == 15.0

    def test_augmentation_without_space(self, valid_employee_data):
        """Format sans espace '15%' aussi nettoyé."""
        valid_employee_data["augementation_salaire_precedente"] = "15%"
        employee = EmployeeInput(**valid_employee_data)
        df = prepare_input(employee)

        assert df["augementation_salaire_precedente"].iloc[0] == 15.0

    def test_frequence_deplacement_mapping(self, valid_employee_data):
        """La fréquence de déplacement doit être mappée en ordinal."""
        mapping = {"Aucun": 0, "Occasionnel": 1, "Frequent": 2}
        for label, expected in mapping.items():
            valid_employee_data["frequence_deplacement"] = label
            employee = EmployeeInput(**valid_employee_data)
            df = prepare_input(employee)
            assert df["frequence_deplacement"].iloc[0] == expected

    def test_ratio_anciennete_age(self, valid_employee_data):
        """ratio_anciennete_age = annees_dans_l_entreprise / age."""
        valid_employee_data["annees_dans_l_entreprise"] = 10
        valid_employee_data["age"] = 40
        employee = EmployeeInput(**valid_employee_data)
        df = prepare_input(employee)

        assert df["ratio_anciennete_age"].iloc[0] == pytest.approx(0.25)

    def test_ratio_stabilite_poste(self, valid_employee_data):
        """ratio_stabilite_poste = annees_poste / annees_entreprise."""
        valid_employee_data["annees_dans_le_poste_actuel"] = 3
        valid_employee_data["annees_dans_l_entreprise"] = 6
        employee = EmployeeInput(**valid_employee_data)
        df = prepare_input(employee)

        assert df["ratio_stabilite_poste"].iloc[0] == pytest.approx(0.5)

    def test_ratio_stabilite_poste_zero_division(self, valid_employee_data):
        """Si annees_entreprise = 0, ratio_stabilite_poste = 0."""
        valid_employee_data["annees_dans_l_entreprise"] = 0
        valid_employee_data["annees_dans_le_poste_actuel"] = 0
        employee = EmployeeInput(**valid_employee_data)
        df = prepare_input(employee)

        assert df["ratio_stabilite_poste"].iloc[0] == 0.0

    def test_revenu_par_annee_age(self, valid_employee_data):
        """revenu_par_annee_age = revenu_mensuel / age."""
        valid_employee_data["revenu_mensuel"] = 5000
        valid_employee_data["age"] = 25
        employee = EmployeeInput(**valid_employee_data)
        df = prepare_input(employee)

        assert df["revenu_par_annee_age"].iloc[0] == pytest.approx(200.0)

    def test_string_columns_preserved(self, valid_employee_data):
        """Les colonnes catégorielles string doivent rester intactes."""
        employee = EmployeeInput(**valid_employee_data)
        df = prepare_input(employee)

        assert df["genre"].iloc[0] == "M"
        assert df["heure_supplementaires"].iloc[0] == "Non"
        assert df["statut_marital"].iloc[0] == "Marié(e)"
        assert df["departement"].iloc[0] == "Consulting"
        assert df["poste"].iloc[0] == "Consultant"
        assert df["domaine_etude"].iloc[0] == "Infra & Cloud"


class TestGetModel:
    """Tests du chargement du modèle."""

    def test_get_model_loads_when_none(self):
        """get_model() appelle load_model() quand _model est None."""
        old_model = ml_service._model
        ml_service._model = None

        mock = MagicMock()
        with patch.object(ml_service, "load_model", return_value=mock) as mock_load:
            ml_service.get_model()
            mock_load.assert_called_once()

        # Cleanup
        ml_service._model = old_model

    def test_get_model_returns_cached(self):
        """get_model() retourne le modèle en cache sans recharger."""
        mock = MagicMock()
        ml_service._model = mock

        with patch.object(ml_service, "load_model") as mock_load:
            result = ml_service.get_model()
            mock_load.assert_not_called()
            assert result is mock

        ml_service._model = None
