# Build context: repository root (see docker-compose.yml).

FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY piecemint/frontend/package.json piecemint/frontend/package-lock.json ./
RUN npm ci
COPY piecemint/frontend/ ./
ARG VITE_API_URL=/api
ARG VITE_MARKETPLACE_URL=http://localhost:5174
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_MARKETPLACE_URL=$VITE_MARKETPLACE_URL
RUN npm run build

FROM python:3.12-slim-bookworm

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN pip install --no-cache-dir pipenv

COPY piecemint/backend/Pipfile piecemint/backend/Pipfile.lock ./
RUN pipenv install --system --deploy

COPY piecemint/backend/ .
COPY --from=frontend-build /frontend/dist ./static

ENV PIECEMINT_STATIC_DIR=/app/static

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
