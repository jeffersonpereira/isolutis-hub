# Imagem única: API + site estático (build do frontend copiado para /app/static).
FROM node:22-alpine AS frontend
WORKDIR /front
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libffi-dev \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    curl \
    && rm -rf /var/lib/apt/lists/*
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir .
COPY backend/alembic.ini ./
COPY backend/migrations ./migrations
COPY --from=frontend /front/dist ./static
ENV HUB_FRONTEND_DIST=/app/static HUB_AMBIENTE=producao
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/api/saude || exit 1
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
