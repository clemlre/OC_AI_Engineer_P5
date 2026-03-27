from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import get_db
from app.models.schemas import HealthResponse
from app.services.ml_service import get_model

router = APIRouter(tags=["Santé"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Vérifie l'état de l'API, du modèle ML et de la connexion DB."""
    # Vérification du modèle
    try:
        model = get_model()
        model_loaded = model is not None
    except Exception:
        model_loaded = False

    # Vérification de la DB
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    status_str = "ok" if model_loaded and db_connected else "degraded"

    return HealthResponse(
        status=status_str,
        model_loaded=model_loaded,
        db_connected=db_connected,
        environment=settings.ENVIRONMENT,
    )
