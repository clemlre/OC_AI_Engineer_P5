import joblib
import pandas as pd

from app.config import settings
from app.models.schemas import EmployeeInput

# Ordre exact des features attendues par le pipeline
FEATURE_ORDER = [
    "age",
    "genre",
    "revenu_mensuel",
    "statut_marital",
    "departement",
    "poste",
    "nombre_experiences_precedentes",
    "annee_experience_totale",
    "annees_dans_l_entreprise",
    "annees_dans_le_poste_actuel",
    "satisfaction_employee_environnement",
    "note_evaluation_precedente",
    "niveau_hierarchique_poste",
    "satisfaction_employee_nature_travail",
    "satisfaction_employee_equipe",
    "satisfaction_employee_equilibre_pro_perso",
    "note_evaluation_actuelle",
    "heure_supplementaires",
    "augementation_salaire_precedente",
    "nombre_participation_pee",
    "nb_formations_suivies",
    "distance_domicile_travail",
    "niveau_education",
    "domaine_etude",
    "frequence_deplacement",
    "annees_depuis_la_derniere_promotion",
    "annes_sous_responsable_actuel",
    "ratio_anciennete_age",
    "ratio_stabilite_poste",
    "revenu_par_annee_age",
]

# Singleton du modèle chargé
_model = None


def load_model():
    """Charge le modèle depuis le fichier joblib."""
    global _model
    _model = joblib.load(settings.MODEL_PATH)
    return _model


def get_model():
    """Retourne le modèle chargé, le charge si nécessaire."""
    global _model
    if _model is None:
        load_model()
    return _model


def prepare_input(employee: EmployeeInput) -> pd.DataFrame:
    """Transforme un EmployeeInput en DataFrame compatible avec le pipeline.

    Reproduit la logique de utils.py:preparer_xy() :
    1. Nettoyage du pourcentage d'augmentation
    2. Mapping ordinal de la fréquence de déplacement
    3. Calcul des 3 features engineerées
    4. Construction du DataFrame dans l'ordre exact des features
    """
    data = employee.model_dump()

    # 1. Nettoyage augementation_salaire_precedente : "11 %" -> 11.0
    aug_str = data["augementation_salaire_precedente"]
    data["augementation_salaire_precedente"] = float(aug_str.rstrip(" %"))

    # 2. Mapping ordinal frequence_deplacement
    mapping_freq = {"Aucun": 0, "Occasionnel": 1, "Frequent": 2}
    data["frequence_deplacement"] = mapping_freq[data["frequence_deplacement"]]

    # 3. Feature engineering
    data["ratio_anciennete_age"] = data["annees_dans_l_entreprise"] / data["age"]

    if data["annees_dans_l_entreprise"] > 0:
        data["ratio_stabilite_poste"] = (
            data["annees_dans_le_poste_actuel"] / data["annees_dans_l_entreprise"]
        )
    else:
        data["ratio_stabilite_poste"] = 0.0

    data["revenu_par_annee_age"] = data["revenu_mensuel"] / data["age"]

    # 4. Construction du DataFrame dans l'ordre exact
    df = pd.DataFrame([data])[FEATURE_ORDER]
    return df


def predict(employee: EmployeeInput) -> tuple[int, float]:
    """Effectue une prédiction d'attrition pour un employé.

    Returns:
        tuple: (prediction 0/1, probabilité de la classe 1)
    """
    model = get_model()
    df = prepare_input(employee)

    prediction = int(model.predict(df)[0])
    probability = float(model.predict_proba(df)[0][1])

    return prediction, probability
