from sqlalchemy.orm import Session

from app.models.orm import ApiKey, Prediction


def log_prediction(
    db: Session,
    input_data: dict,
    prediction: int,
    probability: float,
    api_key_used: str,
    model_version: str = "1.0.0",
) -> Prediction:
    """Enregistre une prédiction dans la base de données."""
    pred = Prediction(
        input_data=input_data,
        prediction=prediction,
        probability=probability,
        model_version=model_version,
        api_key_used=api_key_used,
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    return pred


def get_predictions(db: Session, skip: int = 0, limit: int = 50) -> list[Prediction]:
    """Récupère la liste paginée des prédictions."""
    return (
        db.query(Prediction)
        .order_by(Prediction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_prediction_by_id(db: Session, prediction_id: int) -> Prediction | None:
    """Récupère une prédiction par son ID."""
    return db.query(Prediction).filter(Prediction.id == prediction_id).first()


def get_api_key_by_hash(db: Session, key_hash: str) -> ApiKey | None:
    """Récupère une clé API par son hash."""
    return db.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.is_active).first()
