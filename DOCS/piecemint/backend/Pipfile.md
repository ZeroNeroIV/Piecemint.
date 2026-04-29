# Python dependencies (Pipenv)

**Source file:** `piecemint/backend/Pipfile`

## Overview

- Declares FastAPI, Uvicorn (standard extras), Pydantic, PyYAML, ReportLab, Pandas, SQLAlchemy, MCP, HTTPX, google-genai, etc.

- Setup: `pip install pipenv` then from `piecemint/backend` run `pipenv install` (uses **`Pipfile.lock`** for reproducible installs).

- Run API: `pipenv run python -m uvicorn api.main:app --reload`.
