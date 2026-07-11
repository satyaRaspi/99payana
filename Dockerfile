FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Frontend build. Use npm install instead of npm ci because generated package-lock
# files can contain local/private registry URLs and break Railway/Docker builds.
COPY frontend/package.json ./frontend/package.json
RUN cd frontend \
    && npm config set registry https://registry.npmjs.org/ \
    && npm install --include=dev --no-audit --no-fund

COPY frontend ./frontend
RUN cd frontend && npm run build

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend

WORKDIR /app/backend
ENV STATIC_DIR=/app/frontend/dist
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
