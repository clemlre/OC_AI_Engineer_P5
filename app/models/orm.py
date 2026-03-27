from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Employee(Base):
    """Table stockant le dataset complet des employés."""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    age: Mapped[int] = mapped_column(Integer)
    genre: Mapped[str] = mapped_column(String(10))
    revenu_mensuel: Mapped[int] = mapped_column(Integer)
    statut_marital: Mapped[str] = mapped_column(String(50))
    departement: Mapped[str] = mapped_column(String(50))
    poste: Mapped[str] = mapped_column(String(100))
    nombre_experiences_precedentes: Mapped[int] = mapped_column(Integer)
    annee_experience_totale: Mapped[int] = mapped_column(Integer)
    annees_dans_l_entreprise: Mapped[int] = mapped_column(Integer)
    annees_dans_le_poste_actuel: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_environnement: Mapped[int] = mapped_column(Integer)
    note_evaluation_precedente: Mapped[int] = mapped_column(Integer)
    niveau_hierarchique_poste: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_nature_travail: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_equipe: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_equilibre_pro_perso: Mapped[int] = mapped_column(Integer)
    note_evaluation_actuelle: Mapped[int] = mapped_column(Integer)
    heure_supplementaires: Mapped[str] = mapped_column(String(10))
    augementation_salaire_precedente: Mapped[str] = mapped_column(String(10))
    nombre_participation_pee: Mapped[int] = mapped_column(Integer)
    nb_formations_suivies: Mapped[int] = mapped_column(Integer)
    distance_domicile_travail: Mapped[int] = mapped_column(Integer)
    niveau_education: Mapped[int] = mapped_column(Integer)
    domaine_etude: Mapped[str] = mapped_column(String(100))
    frequence_deplacement: Mapped[str] = mapped_column(String(50))
    annees_depuis_la_derniere_promotion: Mapped[int] = mapped_column(Integer)
    annes_sous_responsable_actuel: Mapped[int] = mapped_column(Integer)
    a_quitte_l_entreprise: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Prediction(Base):
    """Table de log des prédictions effectuées via l'API."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    input_data: Mapped[dict] = mapped_column(JSON)
    prediction: Mapped[int] = mapped_column(Integer)
    probability: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    api_key_used: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class ApiKey(Base):
    """Table de gestion des clés API."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
