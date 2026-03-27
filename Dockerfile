FROM python:3.11-slim

WORKDIR /app

# Installer uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copier les fichiers de dépendances
COPY pyproject.toml uv.lock ./

# Installer les dépendances (sans dev)
RUN uv sync --no-dev --frozen

# Copier le code source
COPY app/ app/
COPY ml_models/ ml_models/
COPY data/ data/
COPY scripts/ scripts/

# Port requis par Hugging Face Spaces
EXPOSE 7860

# Initialiser la DB et lancer le serveur
CMD ["sh", "-c", "uv run python scripts/init_db.py && uv run uvicorn app.main:app --host 0.0.0.0 --port 7860"]
