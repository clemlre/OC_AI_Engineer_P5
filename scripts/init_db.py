"""Script d'initialisation de la base de données.

Crée les tables, insère le dataset depuis les CSV bruts,
et génère une clé API initiale.
"""

import os
import secrets
import sys
from pathlib import Path

import bcrypt
import pandas as pd

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import Base, engine, SessionLocal
from app.models.orm import ApiKey, Employee


def charger_et_fusionner() -> pd.DataFrame:
    """Charge et fusionne les 3 CSV bruts."""
    data_dir = Path(__file__).parent.parent / "data"

    df_sirh = pd.read_csv(data_dir / "extrait_sirh.csv")
    df_eval = pd.read_csv(data_dir / "extrait_eval.csv")
    df_sondage = pd.read_csv(data_dir / "extrait_sondage.csv")

    # Nettoyage eval_number: "E_123" -> 123
    df_eval["id_clean"] = (
        df_eval["eval_number"].astype(str).str.extract(r"(\d+)").astype(int)
    )

    # Fusion SIRH + Eval
    df_merge = pd.merge(
        df_sirh, df_eval, left_on="id_employee", right_on="id_clean",
        how="left", suffixes=("_sirh", "_eval"),
    )

    # Fusion + Sondage
    df_final = pd.merge(
        df_merge, df_sondage, left_on="id_employee", right_on="code_sondage",
        how="left", suffixes=("", "_sondage"),
    )

    # Suppression colonnes techniques
    cols_drop = ["id_clean", "code_sondage", "eval_number"]
    df_final = df_final.drop(columns=[c for c in cols_drop if c in df_final.columns])

    return df_final


def inserer_employees(df: pd.DataFrame):
    """Insère le dataset dans la table employees."""
    db = SessionLocal()
    try:
        # Colonnes à conserver pour la table employees
        colonnes_employee = [
            "age", "genre", "revenu_mensuel", "statut_marital", "departement",
            "poste", "nombre_experiences_precedentes", "annee_experience_totale",
            "annees_dans_l_entreprise", "annees_dans_le_poste_actuel",
            "satisfaction_employee_environnement", "note_evaluation_precedente",
            "niveau_hierarchique_poste", "satisfaction_employee_nature_travail",
            "satisfaction_employee_equipe", "satisfaction_employee_equilibre_pro_perso",
            "note_evaluation_actuelle", "heure_supplementaires",
            "augementation_salaire_precedente", "nombre_participation_pee",
            "nb_formations_suivies", "distance_domicile_travail", "niveau_education",
            "domaine_etude", "frequence_deplacement",
            "annees_depuis_la_derniere_promotion", "annes_sous_responsable_actuel",
            "a_quitte_l_entreprise",
        ]

        # Filtrer les colonnes existantes
        cols_present = [c for c in colonnes_employee if c in df.columns]
        df_insert = df[cols_present].copy()

        # Supprimer les colonnes constantes et IDs (gardées pour la BDD)
        for _, row in df_insert.iterrows():
            employee = Employee(**row.to_dict())
            db.add(employee)

        db.commit()
        print(f"  {len(df_insert)} employés insérés dans la base de données.")
    finally:
        db.close()


def creer_api_key():
    """Génère et insère une clé API initiale."""
    db = SessionLocal()
    try:
        # Générer une clé aléatoire ou utiliser celle de l'env
        raw_key = os.environ.get("INIT_API_KEY", secrets.token_urlsafe(32))
        key_hash = bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        api_key = ApiKey(key_hash=key_hash, name="default")
        db.add(api_key)
        db.commit()

        print(f"  Clé API générée : {raw_key}")
        print("  Conservez cette clé, elle ne sera plus affichée.")
        return raw_key
    finally:
        db.close()


def main():
    print("=== Initialisation de la base de données ===\n")

    # 1. Créer les tables
    print("1. Création des tables...")
    Base.metadata.create_all(bind=engine)
    print("  Tables créées avec succès.\n")

    # 2. Charger et insérer le dataset
    print("2. Chargement et insertion du dataset...")
    df = charger_et_fusionner()
    inserer_employees(df)
    print()

    # 3. Générer la clé API
    print("3. Génération de la clé API...")
    creer_api_key()
    print()

    print("=== Initialisation terminée ===")


if __name__ == "__main__":
    main()
