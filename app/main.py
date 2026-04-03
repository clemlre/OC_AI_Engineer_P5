from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import Base, SessionLocal, engine
from app.models.orm import ApiKey
from app.routers import health, predictions
from app.services.ml_service import load_model


def _seed_api_key(db: Session) -> None:
    """Crée une clé API initiale si aucune n'existe et INIT_API_KEY est défini."""
    if settings.INIT_API_KEY and not db.query(ApiKey).first():
        key_hash = bcrypt.hashpw(
            settings.INIT_API_KEY.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        db.add(ApiKey(key_hash=key_hash, name="initial"))
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Chargement du modèle au démarrage de l'application."""
    # Startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed_api_key(db)
    finally:
        db.close()
    load_model()
    yield
    # Shutdown


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=(
        "API de prédiction d'attrition des employés. "
        "Utilise un modèle Random Forest entraîné sur des données RH, "
        "d'évaluation et de sondage pour prédire si un employé va quitter l'entreprise."
    ),
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(predictions.router)
