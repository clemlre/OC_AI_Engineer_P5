import bcrypt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.orm import ApiKey


def hash_api_key(raw_key: str) -> str:
    """Hash une clé API avec bcrypt."""
    return bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_raw_key(raw_key: str, hashed: str) -> bool:
    """Vérifie une clé brute contre son hash bcrypt."""
    return bcrypt.checkpw(raw_key.encode("utf-8"), hashed.encode("utf-8"))


def verify_api_key(
    x_api_key: str = Header(..., description="Clé API pour l'authentification"),
    db: Session = Depends(get_db),
) -> str:
    """Vérifie la clé API fournie dans le header X-API-Key.

    Parcourt les clés actives et vérifie le hash bcrypt.
    Retourne le hash de la clé utilisée pour le logging.
    """
    active_keys = db.query(ApiKey).filter(ApiKey.is_active).all()

    for api_key in active_keys:
        if verify_raw_key(x_api_key, api_key.key_hash):
            return api_key.key_hash

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Clé API invalide ou inactive.",
    )
