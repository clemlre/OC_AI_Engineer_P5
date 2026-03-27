from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./attrition.db"
    MODEL_PATH: str = "ml_models/best_rf_model.joblib"
    ENVIRONMENT: Literal["dev", "prod"] = "dev"
    API_TITLE: str = "API Prédiction Attrition"
    API_VERSION: str = "1.0.0"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
