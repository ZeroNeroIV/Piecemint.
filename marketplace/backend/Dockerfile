# Build context: repository root (see render.yaml / docker-compose).

FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY marketplace/frontend/package.json marketplace/frontend/package-lock.json ./
RUN npm ci
COPY marketplace/frontend/ ./
ARG VITE_MAIN_APP_URL=http://127.0.0.1:5173
ARG VITE_MARKETPLACE_API_URL=/api
ENV VITE_MAIN_APP_URL=$VITE_MAIN_APP_URL
ENV VITE_MARKETPLACE_API_URL=$VITE_MARKETPLACE_API_URL
RUN npm run build

FROM python:3.12-slim-bookworm

WORKDIR /app/marketplace/backend
ENV PYTHONUNBUFFERED=1

COPY marketplace/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY marketplace/backend/ /app/marketplace/backend/
COPY --from=frontend-build /frontend/dist /app/marketplace/backend/static
COPY piecemint/backend/plugins /app/piecemint/backend/plugins
COPY piecemint/backend/disabled_plugins /app/piecemint/backend/disabled_plugins

ENV MARKETPLACE_STATIC_DIR=/app/marketplace/backend/static

EXPOSE 8000
ENV PORT=8000

CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
