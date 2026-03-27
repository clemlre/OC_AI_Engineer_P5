from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import Base, engine
from app.routers import health, predictions
from app.services.ml_service import load_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Chargement du modèle au démarrage de l'application."""
    # Startup
    Base.metadata.create_all(bind=engine)
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
