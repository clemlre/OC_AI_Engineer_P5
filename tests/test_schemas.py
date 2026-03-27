"""Tests unitaires pour la validation des schemas Pydantic."""

import pytest
from pydantic import ValidationError

from app.models.schemas import EmployeeInput


class TestEmployeeInputValidation:
    """Tests de validation du schema EmployeeInput."""

    def test_valid_input(self, valid_employee_data):
        """Un input valide doit être accepté."""
        employee = EmployeeInput(**valid_employee_data)
        assert employee.age == 35
        assert employee.genre == "M"

    def test_missing_required_field(self, valid_employee_data):
        """Un champ manquant doit lever une erreur."""
        del valid_employee_data["age"]
        with pytest.raises(ValidationError) as exc_info:
            EmployeeInput(**valid_employee_data)
        assert "age" in str(exc_info.value)

    def test_age_too_low(self, valid_employee_data):
        """Un âge inférieur à 18 doit être rejeté."""
        valid_employee_data["age"] = 15
        with pytest.raises(ValidationError):
            EmployeeInput(**valid_employee_data)

    def test_age_too_high(self, valid_employee_data):
        """Un âge supérieur à 65 doit être rejeté."""
        valid_employee_data["age"] = 70
        with pytest.raises(ValidationError):
            EmployeeInput(**valid_employee_data)

    def test_invalid_genre(self, valid_employee_data):
        """Un genre invalide doit être rejeté."""
        valid_employee_data["genre"] = "X"
        with pytest.raises(ValidationError):
            EmployeeInput(**valid_employee_data)

    def test_invalid_departement(self, valid_employee_data):
        """Un département invalide doit être rejeté."""
        valid_employee_data["departement"] = "Finance"
        with pytest.raises(ValidationError):
            EmployeeInput(**valid_employee_data)

    def test_invalid_poste(self, valid_employee_data):
        """Un poste invalide doit être rejeté."""
        valid_employee_data["poste"] = "Stagiaire"
        with pytest.raises(ValidationError):
            EmployeeInput(**valid_employee_data)

    def test_satisfaction_out_of_range(self, valid_employee_data):
        """Une satisfaction hors [1,4] doit être rejetée."""
        valid_employee_data["satisfaction_employee_environnement"] = 5
        with pytest.raises(ValidationError):
            EmployeeInput(**valid_employee_data)

    def test_satisfaction_zero(self, valid_employee_data):
        """Une satisfaction à 0 doit être rejetée."""
        valid_employee_data["satisfaction_employee_equipe"] = 0
        with pytest.raises(ValidationError):
            EmployeeInput(**valid_employee_data)

    def test_invalid_augmentation_format(self, valid_employee_data):
        """Un format d'augmentation invalide doit être rejeté."""
        valid_employee_data["augementation_salaire_precedente"] = "quinze"
        with pytest.raises(ValidationError):
            EmployeeInput(**valid_employee_data)

    def test_valid_augmentation_formats(self, valid_employee_data):
        """Différents formats valides d'augmentation."""
        for fmt in ["11 %", "25 %", "11%", "5 %"]:
            valid_employee_data["augementation_salaire_precedente"] = fmt
            employee = EmployeeInput(**valid_employee_data)
            assert employee.augementation_salaire_precedente == fmt

    def test_invalid_frequence_deplacement(self, valid_employee_data):
        """Une fréquence de déplacement invalide doit être rejetée."""
        valid_employee_data["frequence_deplacement"] = "Très souvent"
        with pytest.raises(ValidationError):
            EmployeeInput(**valid_employee_data)

    def test_invalid_domaine_etude(self, valid_employee_data):
        """Un domaine d'étude invalide doit être rejeté."""
        valid_employee_data["domaine_etude"] = "Médecine"
        with pytest.raises(ValidationError):
            EmployeeInput(**valid_employee_data)

    def test_negative_experience(self, valid_employee_data):
        """Des années d'expérience négatives doivent être rejetées."""
        valid_employee_data["annee_experience_totale"] = -1
        with pytest.raises(ValidationError):
            EmployeeInput(**valid_employee_data)

    def test_all_valid_statuts_maritaux(self, valid_employee_data):
        """Tous les statuts maritaux valides doivent être acceptés."""
        for statut in ["Célibataire", "Marié(e)", "Divorcé(e)"]:
            valid_employee_data["statut_marital"] = statut
            employee = EmployeeInput(**valid_employee_data)
            assert employee.statut_marital == statut
