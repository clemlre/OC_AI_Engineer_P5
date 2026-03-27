from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EmployeeInput(BaseModel):
    """Schéma d'entrée pour la prédiction d'attrition d'un employé.

    Les champs correspondent aux données brutes issues des 3 sources
    (SIRH, Évaluation, Sondage) après suppression des colonnes constantes et IDs.
    """

    age: int = Field(ge=18, le=65, description="Âge de l'employé")
    genre: Literal["F", "M"] = Field(description="Genre (F ou M)")
    revenu_mensuel: int = Field(ge=0, description="Revenu mensuel en euros")
    statut_marital: Literal["Célibataire", "Marié(e)", "Divorcé(e)"] = Field(
        description="Statut marital"
    )
    departement: Literal["Commercial", "Consulting", "Ressources Humaines"] = Field(
        description="Département"
    )
    poste: Literal[
        "Cadre Commercial",
        "Assistant de Direction",
        "Consultant",
        "Tech Lead",
        "Manager",
        "Senior Manager",
        "Représentant Commercial",
        "Directeur Technique",
        "Ressources Humaines",
    ] = Field(description="Poste occupé")
    nombre_experiences_precedentes: int = Field(
        ge=0, description="Nombre d'expériences professionnelles précédentes"
    )
    annee_experience_totale: int = Field(
        ge=0, description="Années d'expérience totale"
    )
    annees_dans_l_entreprise: int = Field(ge=0, description="Années dans l'entreprise")
    annees_dans_le_poste_actuel: int = Field(ge=0, description="Années dans le poste actuel")
    satisfaction_employee_environnement: int = Field(
        ge=1, le=4, description="Satisfaction environnement (1-4)"
    )
    note_evaluation_precedente: int = Field(
        ge=1, le=4, description="Note évaluation précédente (1-4)"
    )
    niveau_hierarchique_poste: int = Field(
        ge=1, le=5, description="Niveau hiérarchique (1-5)"
    )
    satisfaction_employee_nature_travail: int = Field(
        ge=1, le=4, description="Satisfaction nature du travail (1-4)"
    )
    satisfaction_employee_equipe: int = Field(
        ge=1, le=4, description="Satisfaction équipe (1-4)"
    )
    satisfaction_employee_equilibre_pro_perso: int = Field(
        ge=1, le=4, description="Satisfaction équilibre pro/perso (1-4)"
    )
    note_evaluation_actuelle: int = Field(
        ge=3, le=4, description="Note évaluation actuelle (3-4)"
    )
    heure_supplementaires: Literal["Oui", "Non"] = Field(
        description="Fait des heures supplémentaires"
    )
    augementation_salaire_precedente: str = Field(
        pattern=r"^\d{1,2}\s?%$",
        description="Augmentation salariale précédente (ex: '11 %', '25 %')",
    )
    nombre_participation_pee: int = Field(
        ge=0, le=3, description="Participation au PEE (0-3)"
    )
    nb_formations_suivies: int = Field(ge=0, le=6, description="Formations suivies (0-6)")
    distance_domicile_travail: int = Field(
        ge=1, le=29, description="Distance domicile-travail en km"
    )
    niveau_education: int = Field(ge=1, le=5, description="Niveau d'éducation (1-5)")
    domaine_etude: Literal[
        "Infra & Cloud",
        "Transformation Digitale",
        "Marketing",
        "Entrepreunariat",
        "Autre",
        "Ressources Humaines",
    ] = Field(description="Domaine d'étude")
    frequence_deplacement: Literal["Aucun", "Occasionnel", "Frequent"] = Field(
        description="Fréquence de déplacement"
    )
    annees_depuis_la_derniere_promotion: int = Field(
        ge=0, description="Années depuis la dernière promotion"
    )
    annes_sous_responsable_actuel: int = Field(
        ge=0, description="Années sous le responsable actuel"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
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
            ]
        }
    }


class PredictionResponse(BaseModel):
    """Réponse de prédiction."""

    prediction_id: int
    prediction: int = Field(description="0 = Reste, 1 = Quitte")
    probability: float = Field(description="Probabilité de quitter l'entreprise")
    label: str = Field(description="'Reste' ou 'Quitte'")
    timestamp: datetime


class PredictionDetail(PredictionResponse):
    """Détail complet d'une prédiction incluant les données d'entrée."""

    input_data: dict


class HealthResponse(BaseModel):
    """Réponse du endpoint de santé."""

    status: str
    model_loaded: bool
    db_connected: bool
    environment: str
