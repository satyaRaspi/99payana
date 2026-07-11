FROM node:20-bookworm-slim AS frontend-build
WORKDIR /app/frontend
ENV NODE_ENV=development
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --include=dev --no-audit --no-fund
COPY frontend/ ./
RUN ./node_modules/.bin/vite build

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV STATIC_DIR=/app/frontend/dist
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend/ /app/backend/
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
