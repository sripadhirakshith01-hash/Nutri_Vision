# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt tensorflow-cpu

COPY backend /app/backend
COPY class_names.json /app/class_names.json
COPY --from=frontend /src/frontend/dist /app/frontend/dist
COPY ["07_efficientnetV2B0_feature_extract_model_mixed_precision (1).keras", "/app/food101_model.keras"]

WORKDIR /app/backend
ENV MODEL_PATH=/app/food101_model.keras \
    CLASS_NAMES_PATH=/app/class_names.json \
    SERVE_FRONTEND=true \
    PYTHONPATH=/app/backend

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
