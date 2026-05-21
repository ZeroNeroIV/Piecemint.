# 🍃 Piecemint

> Your all-in-one finance tool — dashboards, analytics, invoicing, budgeting, contacts, and a plugin ecosystem.

Built for **Salam Hack** by [**Alameen Sabbah (ZeroNeroIV)**](https://github.com/ZeroNeroIV).  
Design language inspired by **Mastercard** — warm cream canvas, signal orange accents, pill-shaped components, editorial typography.

---

## ✨ Features

- **Dashboard** — real-time financial overview with charts and key metrics
- **Analytics** — income vs. expense trends, category breakdowns, monthly patterns
- **Transactions** — full CRUD with smart AI categorization (via Google Gemini)
- **Contacts** — manage clients & suppliers in one place
- **Budget & Cash Flow** — plan budgets and forecast cash flow
- **Invoicing** — generate & export invoices (PDF, XLSX, DOCX) and email them
- **Tax Calculator** — estimate tax liability with residency rules
- **Stockholders** — track equity holders and ownership
- **Plugin Marketplace** — browse, install, and build plugins to extend functionality
- **Notifications** — email and web push notifications
- **MCP Server** — AI/LLM integration via the Model Context Protocol

---

## 🏗 Architecture

```
piecemint/                 # Core application
├── frontend/             # React SPA (Vite + TypeScript + Tailwind CSS)
└── backend/              # Python FastAPI + SQLAlchemy + SQLite
    ├── api/              # REST API routes and models
    ├── plugins/          # Enabled (auto-loaded) plugins
    └── disabled_plugins/ # Available but not loaded

marketplace/              # Plugin marketplace
├── frontend/             # React SPA (Vite + TypeScript + Tailwind CSS)
└── backend/              # Python FastAPI catalog API
```

### Plugin System

Piecemint has a built-in plugin architecture. Each plugin is a directory with a `manifest.yaml` and `logic.py`. Plugins register their own FastAPI routes under `/api/plugins/<plugin_id>/`. You can install plugins from the marketplace or upload them via the API.

---

## 🚀 Quick Start

### Prerequisites

| Tool        | Version   |
|-------------|-----------|
| Node.js     | 22+       |
| Python      | 3.12–3.14 |
| pipenv      | latest    |
| Docker      | optional  |

### 1. Install Dependencies

```bash
npm run install:all
```

This installs:
- `npm` packages for both frontends
- Python dependencies for both backends (Pipenv + pip)

### 2. Start All Servers (Dev Mode)

```bash
npm run dev
```

This runs all four servers concurrently:

| Service              | URL                         |
|----------------------|-----------------------------|
| Piecemint Frontend   | `http://localhost:5173`     |
| Piecemint Backend    | `http://localhost:8000`     |
| Marketplace Frontend | `http://localhost:5174`     |
| Marketplace Backend  | `http://localhost:8001`     |

### 3. Open the App

Visit [**http://localhost:5173**](http://localhost:5173) — the frontend auto-proxies `/api` requests to the backend.

---

## 🐳 Docker Compose

```bash
docker compose up --build
```

| Service      | URL                          |
|--------------|------------------------------|
| Piecemint    | `http://localhost:8080`      |
| Marketplace  | `http://localhost:9081`      |

---

## ⚙️ Environment Variables

### Piecemint Backend

| Variable                    | Default                          | Description                            |
|-----------------------------|----------------------------------|----------------------------------------|
| `PIECEMINT_DATABASE_URL`    | `sqlite:///./piecemint.db`       | Database connection string             |
| `PIECEMINT_STATIC_DIR`      | —                                | Path to built frontend SPA             |
| `GOOGLE_API_KEY`            | —                                | Google AI key (smart categorization)   |
| `GEMINI_MODEL`              | `gemma-4-31b-it`                 | AI model for categorization            |
| `FF_SMTP_HOST` / `PORT` / … | —                                | SMTP email configuration               |
| `FF_VAPID_PUBLIC_KEY`       | —                                | Web Push notifications                 |
| `FF_DISABLE_PLUGIN_UPLOAD`  | —                                | Set `1` to block plugin uploads        |
| `FF_PROTECTED_PLUGINS`      | `invoice_gen,...`                | Plugins protected from deletion        |
| `PORT`                      | `8000`                           | Server port                            |

### Piecemint Frontend

| Variable               | Default                        | Description                 |
|------------------------|--------------------------------|-----------------------------|
| `VITE_API_URL`         | `/api`                         | Backend API base URL        |
| `VITE_MARKETPLACE_URL` | `http://localhost:5174`        | Marketplace app URL         |

See `piecemint/frontend/.env.example` and `piecemint/backend/.env.example`.

---

## 🧪 Running Individual Services

```bash
# Piecemint frontend
npm run piecemint-fe                    # dev server (port 5173)
npm run piecemint-fe:build              # production build
npm run piecemint-fe:lint               # lint

# Piecemint backend
npm run piecemint-be                    # uvicorn (port 8000)

# Marketplace frontend
npm run marketplace-fe                  # dev server (port 5174)
npm run marketplace-fe:build            # production build

# Marketplace backend
npm run marketplace-be                  # uvicorn (port 8001)
```

---

## 🤖 MCP Server

Piecemint ships with a Model Context Protocol server (`piecemint/backend/mcp_server.py`) for AI/LLM integration. It exposes tools for reading/writing financial data, sending emails, and generating invoices. Compatible with Cursor, Claude, and any MCP-compatible assistant.

---

## 📄 License

[MIT](LICENSE) © Alameen Sabbah
