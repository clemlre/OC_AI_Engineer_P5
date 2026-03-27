from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.middleware.auth import verify_api_key
from app.models.database import get_db
from app.models.schemas import EmployeeInput, PredictionDetail, PredictionResponse
from app.services import db_service, ml_service

router = APIRouter(prefix="/api/v1", tags=["Prédictions"])


@router.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
def predict(
    employee: EmployeeInput,
    db: Session = Depends(get_db),
    api_key_hash: str = Depends(verify_api_key),
):
    """Effectue une prédiction d'attrition pour un employé.

    Accepte les données d'un employé, retourne la prédiction (Reste/Quitte)
    et la probabilité associée. L'appel est loggé en base de données.
    """
    # Prédiction
    prediction, probability = ml_service.predict(employee)

    # Log en base
    pred_record = db_service.log_prediction(
        db=db,
        input_data=employee.model_dump(),
        prediction=prediction,
        probability=probability,
        api_key_used=api_key_hash,
    )

    return PredictionResponse(
        prediction_id=pred_record.id,
        prediction=prediction,
        probability=round(probability, 4),
        label="Quitte" if prediction == 1 else "Reste",
        timestamp=pred_record.created_at,
    )


@router.get("/predictions", response_model=list[PredictionResponse])
def list_predictions(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(50, ge=1, le=100, description="Nombre max d'éléments"),
    db: Session = Depends(get_db),
    api_key_hash: str = Depends(verify_api_key),
):
    """Retourne la liste paginée des prédictions effectuées."""
    predictions = db_service.get_predictions(db, skip=skip, limit=limit)
    return [
        PredictionResponse(
            prediction_id=p.id,
            prediction=p.prediction,
            probability=round(p.probability, 4),
            label="Quitte" if p.prediction == 1 else "Reste",
            timestamp=p.created_at,
        )
        for p in predictions
    ]


@router.get("/predictions/{prediction_id}", response_model=PredictionDetail)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    api_key_hash: str = Depends(verify_api_key),
):
    """Retourne le détail d'une prédiction par son ID."""
    pred = db_service.get_prediction_by_id(db, prediction_id)
    if pred is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prédiction {prediction_id} non trouvée.",
        )

    return PredictionDetail(
        prediction_id=pred.id,
        prediction=pred.prediction,
        probability=round(pred.probability, 4),
        label="Quitte" if pred.prediction == 1 else "Reste",
        timestamp=pred.created_at,
        input_data=pred.input_data,
    )
