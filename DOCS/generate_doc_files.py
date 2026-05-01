#!/usr/bin/env python3
"""One-off generator: creates DOCS/piecemint/**/<name>.md for each mapped source file."""
from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "piecemint")

# relpath under piecemint/ -> (title, sections as list of str)
SPECS: dict[str, tuple[str, list[str]]] = {
    "backend/api/__init__.py": (
        "Package marker: `api`",
        [
            "Marks `api` as a Python package so imports like `from api.main import app` resolve when the backend working directory is `piecemint/backend`.",
            "No runtime logic; safe to leave minimal or empty.",
        ],
    ),
    "backend/api/main.py": (
        "FastAPI application entrypoint",
        [
            "Creates the `FastAPI` app, registers CORS, runs **lifespan**: `init_db()` + `ensure_seed_data()` on startup.",
            "Loads **PluginManager**: discovers `plugins/*/`, registers each plugin router under `/api/plugins`.",
            "Mounts **core_router** (`/api/core/*`) and defines `GET /` and `GET /api/plugins` (installed vs available plugin metadata).",
            "Run with: `pipenv run python -m uvicorn api.main:app` from `piecemint/backend` (after `pipenv install`).",
        ],
    ),
    "backend/api/core_routes.py": (
        "Core REST API (single workspace)",
        [
            "Router prefix: `/api/core`.",
            "Uses **`DbSession`** and **`WorkspaceScopeId`**: all rows are scoped to the primary org FK (self-hosted; no header pickers).",
            "`GET /workspace` returns the org row id and display name.",
            "Exposes CRUD-style routes for **clients**, **suppliers**, **transactions**, and **stockholders** against SQLAlchemy models.",
            "Returns Pydantic models from `api/models.py` for OpenAPI-friendly responses.",
        ],
    ),
    "backend/api/database.py": (
        "SQLAlchemy engine and session factory",
        [
            "Defines SQLAlchemy **`Base`**, **`engine`**, and **`SessionLocal`**.",
            "Default DB: SQLite at `piecemint/backend/piecemint.db` unless `PIECEMINT_DATABASE_URL` is set.",
            "**`get_db()`** is a FastAPI dependency generator yielding a session (close in `finally`).",
            "**`init_db()`** imports `api.db_models` (to register tables) and runs `Base.metadata.create_all(bind=engine)`.",
        ],
    ),
    "backend/api/db_models.py": (
        "ORM models: org row + finance tables",
        [
            "**`Tenant`**: org/workspace master row (`tenants.id`). Child tables use FK column `tenant_id` (name unchanged for DB compatibility).",
            "**`Client`**, **`Supplier`**, **`Transaction`**, **`Stockholder`**: scoped by that FK with business fields matching the API/seed data.",
            "**`Transaction`**: stores `date` / `last_activity` as strings (ISO dates) for simple JSON alignment with the frontend.",
            "Uses SQLAlchemy 2.0 `Mapped[]` / `mapped_column` style.",
        ],
    ),
    "backend/api/deps.py": (
        "FastAPI dependencies: DB session and workspace scope",
        [
            "**`get_workspace_scope_id`**: returns the primary org FK (`PRIMARY_WORKSPACE_ROW_ID`) for this deployment.",
            "**`WorkspaceScopeId`**: `Annotated[str, Depends(get_workspace_scope_id)]` for concise route parameters.",
            "**`DbSession`**: `Annotated[Session, Depends(get_db)]` for SQLAlchemy sessions per request.",
        ],
    ),
    "backend/api/models.py": (
        "Pydantic request/response models",
        [
            "Defines API shapes: **`Client`**, **`Supplier`**, **`Transaction`**, **`Stockholder`**, plus **`*Create`** bodies where applicable.",
            "**`WorkspaceSummary`**: `id` + `name` for `GET /api/core/workspace`.",
            "**`EmailNotificationTestBody`**: JSON body for **`POST /api/plugins/email_notifications/test`** (declared here so Pydantic resolves correctly when `email_notifications` is loaded as a dynamic plugin).",
            "Used for response validation and OpenAPI schema in `core_routes.py`.",
        ],
    ),
    "backend/api/seed.py": (
        "Initial data seed (idempotent)",
        [
            "**`ensure_seed_data(db)`** runs only when the `tenants` table is empty.",
            "Inserts one org row and sample clients, suppliers, transactions, and stockholders for the default demo workspace.",
            "Called from **`api/main.py`** lifespan at startup so demos work without manual SQL.",
        ],
    ),
    "backend/api/workspace_data.py": (
        "Read model for plugins (dict compatibility)",
        [
            "**`ensure_org_row`**: creates a **`Tenant`** ORM row if an unknown org id is used.",
            "**`get_workspace_data(db, org_row_id)`** returns `clients`, `suppliers`, `transactions` as plain dict lists (legacy mock `DB` shape).",
            "**`primary_org_fk`** supports MCP callers that resolve the first org row.",
            "Imported by plugin `logic.py` files for tax, expenses, and AI without duplicating query logic.",
        ],
    ),
    "backend/plugin_manager.py": (
        "Dynamic plugin discovery and registration",
        [
            "Scans **`plugins/`** for subfolders with **`manifest.yaml`**.",
            "For each plugin with **`logic.py`**, loads the module and collects **`router`** objects; registers them on the app under prefix **`/api/plugins`**.",
            "**`apply_mcp_extras(mcp)`** loads optional **`mcp_extras.py`** (same manifest-gated folders) and calls **`register_mcp(mcp)`** if present; failures are logged per plugin. Used by **`mcp_server.py`** only (not FastAPI startup).",
            "**`get_installed_plugins()`** re-reads the filesystem for the marketplace UI; **`get_available_plugins()`** lists folders under **`disabled_plugins/`** (MCP extras are not loaded from disabled plugins).",
            "Note: moving a plugin only updates HTTP routes after the app process reloads; the plugin **list** can update without restart.",
        ],
    ),
    "backend/mcp_server.py": (
        "MCP (Model Context Protocol) stdio server",
        [
            "Uses **`mcp.server.fastmcp.FastMCP`** with **`mcp.run()`** (stdio transport) for Cursor/OpenCode/Claude Desktop style hosts.",
            "Shares the same SQLite file as the FastAPI app via **`api.database`** (run from **`piecemint/backend`** so paths match).",
            "Core tools (workspace via **`primary_org_fk`**): **`get_clients`**, **`get_stockholders`**, **`add_stockholder`**, **`list_transactions`**, **`email_and_invoice_capabilities`**, **`send_email`**, **`send_invoice_email`** (invoice helpers load only if **`invoice_gen`** is present).",
            "**`send_invoice_email`** reads ORM **`Client`** fields inside the DB session before calling **`render_invoice`** (avoids **`DetachedInstanceError`** after **`session_scope()`** exits).",
            "**`PluginManager().apply_mcp_extras(mcp)`** runs after builtins; optional per-plugin **`mcp_extras.py`** implementations populate **`plugin_mcp_extras_loaded`** in **`email_and_invoice_capabilities`**.",
            "Entry: `pipenv run python mcp_server.py` from `piecemint/backend`.",
        ],
    ),
    "backend/Pipfile": (
        "Python dependencies (Pipenv)",
        [
            "Declares FastAPI, Uvicorn (standard extras), Pydantic, PyYAML, ReportLab, Pandas, SQLAlchemy, MCP, HTTPX, google-genai, etc.",
            "Setup: `pip install pipenv` then from `piecemint/backend` run `pipenv install` (uses **`Pipfile.lock`** for reproducible installs).",
            "Run API: `pipenv run python -m uvicorn api.main:app --reload`.",
        ],
    ),
    "backend/Pipfile.lock": (
        "Pipenv lockfile",
        [
            "Resolved dependency graph; use **`pipenv install --deploy`** in CI for reproducible installs.",
            "**Do not hand-edit**; regenerate with **`pipenv lock`** after changing the Pipfile.",
        ],
    ),
    "backend/plugins/tax_calculator/logic.py": (
        "Plugin: tax calculator (endpoint implementation)",
        [
            "Router mounted at **`/api/plugins/tax_calculator/...`** (see `plugin_manager` prefix).",
            "**`GET /tax_calculator/estimate`**: uses **`get_workspace_data`** to sum income transactions and apply `tax_rate` (default 0.2); returns `total_income`, `tax_rate`, `tax_reserve`.",
        ],
    ),
    "backend/plugins/tax_calculator/manifest.yaml": (
        "Plugin: tax calculator (manifest)",
        [
            "Metadata: `name`, `description`, `version` for the marketplace and discovery list.",
        ],
    ),
    "backend/plugins/invoice_gen/logic.py": (
        "Plugin: PDF invoice generation",
        [
            "**`GET /invoice_gen/generate/{client_id}`** loads a **`Client`** for the scoped workspace, returns **`application/pdf`** (ReportLab canvas).",
            "404 if the client id does not exist in this workspace.",
        ],
    ),
    "backend/plugins/invoice_gen/manifest.yaml": (
        "Plugin: invoice generator (manifest)",
        [
            "Metadata for the Invoice Generator plugin in **`/api/plugins`** listing.",
        ],
    ),
    "backend/plugins/expense_categorizer/logic.py": (
        "Plugin: keyword-based expense search",
        [
            "**`GET /expense_categorizer/search?query=...`**: filters expense transactions using simple keyword rules (e.g. \"cloud\" → AWS/Azure/Vercel).",
            "Uses **`get_workspace_data`** for a consistent finance read model.",
        ],
    ),
    "backend/plugins/expense_categorizer/manifest.yaml": (
        "Plugin: Smart Categorizer (manifest)",
        [
            "Metadata for the Smart Categorizer plugin.",
        ],
    ),
    "backend/disabled_plugins/ai_prediction/logic.py": (
        "Plugin: AI cashflow forecast (optional / disabled copy)",
        [
            "Same role as a plugin under `plugins/`, but this copy lives in **`disabled_plugins/`** so it does not load until moved.",
            "**`GET /ai_prediction/forecast`**: Pandas groups transactions by month, mean monthly flow, projects three future months (moving-average style).",
        ],
    ),
    "backend/disabled_plugins/ai_prediction/manifest.yaml": (
        "Plugin: AI prediction (manifest, disabled copy)",
        [
            "Metadata used when the folder is under `plugins/` or when documenting available vs installed in `disabled_plugins/`.",
        ],
    ),
    "backend/api/dev_routes.py": (
        "Development-only routes (plugin install)",
        [
            "**`/api/dev/plugins/install`** and **`install_zip`**: write plugin folders under **`plugins/<id>/`** from pasted Python or a marketplace-style zip.",
            "Guarded by env (e.g. upload disable flags); restart API to load new plugin routers.",
        ],
    ),
    "backend/api/smtp_outbound.py": (
        "Outbound SMTP helper",
        [
            "Sends mail using host/port/user/password TLS settings; used by invoice-by-email and email-notification flows.",
        ],
    ),
    "backend/api/workspace_scope.py": (
        "Workspace constants",
        [
            "Defines **`PRIMARY_WORKSPACE_ROW_ID`** (FK value for child rows / SMTP store keys).",
        ],
    ),
    "backend/api/mock_finance_data.py": (
        "Demo seed data factories",
        [
            "**`all_seed_rows()`** yields SQLAlchemy model instances for **`api.seed`** (tenants, clients, suppliers, transactions, stockholders).",
        ],
    ),
    "backend/plugins/email_notifications/logic.py": (
        "Plugin: email notifications (API)",
        [
            "Persists app-saved SMTP settings (keyed by org FK) and exposes **`/api/plugins/email_notifications/...`**.",
        ],
    ),
    "backend/plugins/email_notifications/manifest.yaml": (
        "Plugin: email notifications (manifest)",
        [
            "Plugin id and metadata for marketplace and plugin manager discovery.",
        ],
    ),
    "backend/plugins/stockholders/logic.py": (
        "Plugin: stockholders (API)",
        [
            "Reserved plugin router; UI uses core **`/api/core/stockholders`** routes.",
        ],
    ),
    "backend/plugins/stockholders/manifest.yaml": (
        "Plugin: stockholders (manifest)",
        [
            "Metadata for the Stockholders plugin.",
        ],
    ),
    "backend/plugins/small_business/logic.py": (
        "Plugin: small business suite (API)",
        [
            "Serves checklist / suite content for the Small business plugin page.",
        ],
    ),
    "backend/plugins/small_business/manifest.yaml": (
        "Plugin: small business (manifest)",
        [
            "Metadata for the Small business plugin.",
        ],
    ),
    "backend/plugins/web_notifications/logic.py": (
        "Plugin: web notifications (API)",
        [
            "Browser notification permission / placeholder endpoints for future Web Push wiring.",
        ],
    ),
    "backend/plugins/web_notifications/manifest.yaml": (
        "Plugin: web notifications (manifest)",
        [
            "Metadata for the Web notifications plugin.",
        ],
    ),
    "backend/plugins/invoice_gen/builders.py": (
        "Invoice export builders (xlsx / docx)",
        [
            "Builds non-PDF exports from invoice document payloads where supported.",
        ],
    ),
    "backend/plugins/invoice_gen/schemas.py": (
        "Invoice plugin Pydantic models",
        [
            "Structured bodies for generate/email endpoints and document validation.",
        ],
    ),
    "backend/plugins/invoice_gen/invoice_document_render.py": (
        "Invoice layout / rendering helpers",
        [
            "Shared rendering helpers for PDF or structured invoice output (ReportLab, fields, numbering).",
        ],
    ),
    "backend/.env.example": (
        "Environment template (backend)",
        [
            "Documents **GOOGLE_API_KEY**, **GEMINI_MODEL**, and optional SMTP-related **`FF_SMTP_*`** vars; copy to **`.env`** locally.",
        ],
    ),
    "frontend/index.html": (
        "Vite HTML shell",
        [
            "Root document for the SPA: mounts **`src/main.tsx`**, includes page title and favicon link.",
            "Vite injects the bundled script during `npm run build` / dev server.",
        ],
    ),
    "frontend/package.json": (
        "npm package manifest (frontend)",
        [
            "Scripts: `dev`, `build`, `lint`, `preview`.",
            "Dependencies: React, Vite, TypeScript, Tailwind v4 (`@tailwindcss/vite`), Recharts, Axios, React Router, Lucide icons.",
        ],
    ),
    "frontend/package-lock.json": (
        "npm lockfile",
        [
            "Exact resolved versions of the dependency tree. **Do not hand-edit**; regenerate with `npm install`.",
            "Commit in version control for reproducible installs across machines and CI.",
        ],
    ),
    "frontend/README.md": (
        "Create Vite + React template README (upstream)",
        [
            "This file in `piecemint/frontend/` is the default Vite React-TS README from the scaffold (dev commands, Vite links).",
            "For Piecemint-specific architecture, see `DOCS/piecemint/README.md` and the per-file `*.md` files in this tree.",
        ],
    ),
    "frontend/vite.config.ts": (
        "Vite configuration",
        [
            "Registers **`@vitejs/plugin-react`** and **`@tailwindcss/vite`** for Tailwind 4 single-file CSS pipeline.",
            "Standard `defineConfig` export for the Piecemint frontend build.",
        ],
    ),
    "frontend/tsconfig.json": (
        "TypeScript project references (root)",
        [
            "Points to **`tsconfig.app.json`** and **`tsconfig.node.json`** via `references` (solution-style layout).",
        ],
    ),
    "frontend/tsconfig.app.json": (
        "TypeScript config for application source",
        [
            "Compiler options for **`src/**`**: JSX, module resolution, strictness suitable for the React app.",
        ],
    ),
    "frontend/tsconfig.node.json": (
        "TypeScript config for Node tooling (Vite config, etc.)",
        [
            "Separate smaller options scope for Vite/Node-side TS files (e.g. `vite.config.ts`).",
        ],
    ),
    "frontend/tailwind.config.js": (
        "Tailwind theme extension (v3-style file; v4 may also use CSS `@theme`)",
        [
            "Extends `theme` with Piecemint color tokens: canvas cream, lifted cream, ink black, signal orange, etc.",
            "If using Tailwind v4 with `@import \"tailwindcss\"` in CSS, this file may be partially redundant; kept for editor/tooling compatibility in some setups.",
        ],
    ),
    "frontend/eslint.config.js": (
        "ESLint flat config",
        [
            "Lint rules for TypeScript + React; used by `npm run lint` and the IDE.",
        ],
    ),
    "frontend/src/main.tsx": (
        "React bootstrap",
        [
            "Creates the root with **`createRoot`**, imports **`index.css`**, renders **`<App />`** in strict mode.",
        ],
    ),
    "frontend/src/index.css": (
        "Global styles and design system base",
        [
            "Imports **Google Font (Sofia Sans)** and Tailwind 4: **`@import \"tailwindcss\"`**.",
            "Defines **CSS variables** and `@theme` colors aligned with the Mastercard-inspired design doc.",
            "Utility classes: **`.pill-button`**, **`.card`**, **`.nav-pill`**, etc., shared across pages.",
        ],
    ),
    "frontend/src/App.css": (
        "Component-scoped default styles (Vite template)",
        [
            "Default Vite/React starter rules for the root logo layout; the app may rely more on `index.css` and Tailwind.",
            "Safe to trim if unused, but still part of the scaffold.",
        ],
    ),
    "frontend/src/App.tsx": (
        "Root React component: router and data provider",
        [
            "Wraps the app in **`BrowserRouter`**, **`FinanceDataProvider`**, and **`Routes`** with **`AppLayout`** as the parent route.",
            "Routes: **`/`** Overview, **`/analytics`**, **`/contacts`**, **`/activity`**, **`/budget`**, **`/financial-settings`**, **`/prices`**, **`/library`**, redirects **`/marketplace`** → **`/library`**, **`/docs/plugins`**, **`/plugin/:pluginId`**.",
        ],
    ),
    "frontend/src/pages/Overview.tsx": (
        "Overview dashboard page",
        [
            "Landing KPIs and charts using **`useFinanceData`**; links into analytics and activity.",
            "Loads finance data via shared API client / context (implicit single workspace).",
        ],
    ),
    "frontend/src/pages/Analytics.tsx": (
        "Cash & analytics page",
        [
            "Deeper charts and breakdowns (Recharts) over transactions and entity totals.",
        ],
    ),
    "frontend/src/pages/Contacts.tsx": (
        "Clients & suppliers directory",
        [
            "Tables with **`EntityCategorySelect`**; **`+`** opens **`AddContactEntityModal`** posting to **`/api/core/clients`** or **`suppliers`**.",
            "Optional invoice download when Invoice Generator plugin is active.",
        ],
    ),
    "frontend/src/pages/Activity.tsx": (
        "Transactions & alerts page",
        [
            "Transaction list, paging, recurring “zombie” hints, plugin-gated expense search.",
        ],
    ),
    "frontend/src/pages/BudgetCashFlow.tsx": (
        "Budget & cash flow page",
        [
            "Budget model in local storage + monthly ledger one-time entries; category mix and scheduled bills UI.",
        ],
    ),
    "frontend/src/pages/Marketplace.tsx": (
        "Plugin library page",
        [
            "**`GET /api/plugins`** for installed vs available; enable toggles, delete dev plugins, **`AddPluginModal`** zip/paste install to **`/api/dev/...`**.",
        ],
    ),
    "frontend/src/pages/PricingPage.tsx": (
        "Prices / plans page",
        [
            "Route **`/prices`**: marketing-style tiers **Free** (core only), **Pro** (**$15/mo**, free plugins + paid plugin add‑ons), **Enterprise** (**Contact us**).",
        ],
    ),
    "frontend/src/pages/PluginDocsPage.tsx": (
        "In-app plugin documentation",
        [
            "Route **`/docs/plugins`**: static copy for plugin layout (**`manifest.yaml`**, **`logic.py`**, optional **`mcp_extras.py`**), REST prefix **`/api/plugins`**, UI enablement, uploads, and Piecemint MCP **`register_mcp`** extension point.",
        ],
    ),
    "frontend/src/pages/PluginPage.tsx": (
        "Per-plugin dashboard",
        [
            "Dynamic route **`/plugin/:pluginId`**: settings panels (invoice, tax, email, stockholders, etc.) when plugin is installed.",
        ],
    ),
    "frontend/src/context/FinanceDataContext.tsx": (
        "Global finance + plugin state",
        [
            "Loads **clients, suppliers, transactions, stockholders, plugins** from **`/api/core/*`** and **`/api/plugins`**; **`refresh()`** re-fetches.",
            "Category registry/taxonomy, invoice export config, smart categorization, invoice download/email helpers.",
        ],
    ),
    "frontend/src/components/AppLayout.tsx": (
        "App chrome: header, sidebar, search",
        [
            "Floating Piecemint header, collapsible sidebar rail, mobile nav; **`GlobalSearchModal`** (⌘K); core sidebar includes **`/prices`**.",
        ],
    ),
    "frontend/src/components/AddContactEntityModal.tsx": (
        "Create client or supplier modal",
        [
            "Portaled dialog; POST **`/api/core/clients`** or **`suppliers`**, then **`refresh()`**.",
        ],
    ),
    "frontend/src/components/AddPluginModal.tsx": (
        "Install plugin from zip or paste",
        [
            "Full-screen flow portaled to **`#ff-overlay-root`**; calls dev install endpoints.",
        ],
    ),
    "frontend/src/components/ContactEntityShowModal.tsx": (
        "Read-only contact detail modal",
        [
            "Shows id, name, email, total billed for a client or supplier row.",
        ],
    ),
    "frontend/src/components/DynamicTaxFieldsForm.tsx": (
        "Dynamic tax field inputs",
        [
            "Renders jurisdiction-specific inputs driven by tax residency config.",
        ],
    ),
    "frontend/src/components/EmailNotificationsPanel.tsx": (
        "Email notifications plugin UI",
        [
            "SMTP settings and test send against **`email_notifications`** API routes.",
        ],
    ),
    "frontend/src/components/EntityCategorySelect.tsx": (
        "Category picker for an entity",
        [
            "Client/supplier/transaction/stockholder kinds; reads/writes **`categoryStorage`** assignments.",
        ],
    ),
    "frontend/src/components/GlobalSearchModal.tsx": (
        "Global ⌘K search modal",
        [
            "Shortcut-driven modal for jumping to routes or records; high z-index shell; **`CORE_ITEMS`** lists pages including **`/prices`**.",
        ],
    ),
    "frontend/src/components/InvoiceDocumentForm.tsx": (
        "Invoice document editor (line items, customer block)",
        [
            "Form sections bound to **`InvoiceDocument`** shape used in export settings.",
        ],
    ),
    "frontend/src/components/InvoiceDownloadModal.tsx": (
        "Invoice download / email modal",
        [
            "Chooses format, edits **`InvoiceExportConfig`**, triggers blob download or email POST.",
        ],
    ),
    "frontend/src/components/InvoiceExportForm.tsx": (
        "Invoice export options form",
        [
            "Output format and document fields shared with download flow.",
        ],
    ),
    "frontend/src/components/InvoiceExportSettings.tsx": (
        "Invoice settings section on plugin page",
        [
            "Wraps export form + persistence for invoice generator defaults.",
        ],
    ),
    "frontend/src/components/InvoiceHistorySection.tsx": (
        "Issued invoice history table",
        [
            "Reads/writes **`invoiceHistoryStorage`**; titles and list UX.",
        ],
    ),
    "frontend/src/components/PluginEnableSwitch.tsx": (
        "Plugin on/off toggle",
        [
            "Reflects **`pluginToggles`** in local storage vs installed plugins.",
        ],
    ),
    "frontend/src/components/SearchableCountrySelect.tsx": (
        "Country combobox",
        [
            "Searchable select for invoice/tax country fields.",
        ],
    ),
    "frontend/src/components/SmallBusinessPanel.tsx": (
        "Small business plugin panel",
        [
            "Displays suite data from **`smallBusinessSuite`** and plugin API.",
        ],
    ),
    "frontend/src/components/SmartCategorizeToolbar.tsx": (
        "Smart categorization actions",
        [
            "Triggers **`runSmartCategorize`** via expense_categorizer plugin.",
        ],
    ),
    "frontend/src/components/StockholdersPanel.tsx": (
        "Stockholders plugin panel",
        [
            "Lists equity holders; uses stockholders core/plugin data.",
        ],
    ),
    "frontend/src/components/TaxCalculatorResidencyPanel.tsx": (
        "Tax calculator residency UI",
        [
            "Persists residency choice affecting tax plugin behavior.",
        ],
    ),
    "frontend/src/components/TaxResidencySection.tsx": (
        "Tax residency section wrapper",
        [
            "Groups residency controls in settings flows.",
        ],
    ),
    "frontend/src/components/TransactionShowModal.tsx": (
        "Transaction detail modal",
        [
            "Read-only view for a single transaction record.",
        ],
    ),
    "frontend/src/components/WebNotificationsPanel.tsx": (
        "Web notifications plugin panel",
        [
            "Permission prompts and status for browser notifications.",
        ],
    ),
    "frontend/src/lib/apiBase.ts": (
        "API base URL",
        [
            "**`VITE_API_URL`** or default **`http://localhost:8000/api`** prefix for axios.",
        ],
    ),
    "frontend/src/lib/budgetStorage.ts": (
        "Budget localStorage persistence",
        [
            "Serializes budget/cashflow state for Budget page.",
        ],
    ),
    "frontend/src/lib/categoryStorage.ts": (
        "Category registry + assignments",
        [
            "localStorage-backed label registry and per-entity category maps for Smart Categorizer UX.",
        ],
    ),
    "frontend/src/lib/categoryTaxonomy.ts": (
        "Entity kind taxonomy",
        [
            "Types/helpers for client/supplier/transaction/stockholder category keys.",
        ],
    ),
    "frontend/src/lib/financeCharts.ts": (
        "Chart helpers",
        [
            "Transforms finance rows for Recharts (overview/analytics).",
        ],
    ),
    "frontend/src/lib/invoiceExportStorage.ts": (
        "Invoice export defaults storage",
        [
            "Persists **`InvoiceExportConfig`** in localStorage.",
        ],
    ),
    "frontend/src/lib/invoiceHistoryStorage.ts": (
        "Invoice history entries",
        [
            "Append/list/update issued invoice metadata for the history table.",
        ],
    ),
    "frontend/src/lib/invoiceNumber.ts": (
        "Invoice numbering helpers",
        [
            "Sequence bump/peek for next invoice numbers in the client.",
        ],
    ),
    "frontend/src/lib/invoiceTemplates.ts": (
        "Invoice template presets",
        [
            "Preset document fragments or defaults for invoice UI.",
        ],
    ),
    "frontend/src/lib/localStorageScope.ts": (
        "Namespaced localStorage keys",
        [
            "Migrates legacy localStorage key suffixes; single-workspace deployments use unprefixed keys.",
        ],
    ),
    "frontend/src/lib/marketplaceUrl.ts": (
        "Public marketplace URL",
        [
            "Constant or env for linking to the external plugin marketplace site from the app header.",
        ],
    ),
    "frontend/src/lib/pluginToggles.ts": (
        "Plugin enable flags storage",
        [
            "Loads/saves which installed plugins are toggled on in the UI.",
        ],
    ),
    "frontend/src/lib/taxCalculatorResidencyStorage.ts": (
        "Tax residency storage",
        [
            "Persists calculator residency selection client-side.",
        ],
    ),
    "frontend/src/types/budget.ts": (
        "Budget TypeScript types",
        [
            "Shapes for Budget & cash flow page state.",
        ],
    ),
    "frontend/src/types/invoiceDocument.ts": (
        "Invoice document types",
        [
            "Structured invoice body (customer, line items, dates).",
        ],
    ),
    "frontend/src/types/invoiceExport.ts": (
        "Invoice export config types",
        [
            "Format, document payload, and API mapping helpers.",
        ],
    ),
    "frontend/src/types/plugins.ts": (
        "Plugin metadata types",
        [
            "Installed vs available plugin rows from **`/api/plugins`**.",
        ],
    ),
    "frontend/src/config/meTaxResidency.config.ts": (
        "Tax residency field config",
        [
            "Declarative fields for ME (or template) residency forms in **`DynamicTaxFieldsForm`**.",
        ],
    ),
    "frontend/src/data/smallBusinessSuite.ts": (
        "Small business checklist data",
        [
            "Static suite items for **`SmallBusinessPanel`** presentation.",
        ],
    ),
    "frontend/src/services/taxResidencyRegistry.ts": (
        "Tax residency registry service",
        [
            "Lookup/registry for residency options used by tax UI.",
        ],
    ),
    "frontend/public/favicon.svg": (
        "Favicon (SVG asset)",
        [
            "Served as `/favicon.svg` from the static `public/` folder. Referenced in `index.html` for browser tab icon.",
        ],
    ),
    "frontend/public/icons.svg": (
        "Sprite or icon set (SVG asset)",
        [
            "Static asset under `public/`; may be used for app icons or embedded symbols depending on the template setup.",
        ],
    ),
}


def main() -> None:
    for rel, (title, bullets) in SPECS.items():
        path = os.path.join(DOCS, rel)
        parent = os.path.dirname(path)
        base = os.path.basename(rel)  # e.g. main.py, App.tsx, README.md
        # Unambiguous: main.py -> main.py.md, App.tsx -> App.tsx.md (avoids App.css vs App.tsx clash)
        if base.endswith(".md") and "README" in base.upper():
            out = os.path.join(parent, base)  # README.md about README
        else:
            out = os.path.join(parent, f"{base}.md")

        os.makedirs(os.path.dirname(out), exist_ok=True)
        lines = [
            f"# {title}",
            "",
            f"**Source file:** `piecemint/{rel}`",
            "",
            "## Overview",
            "",
        ]
        for b in bullets:
            lines.append(f"- {b}")
            lines.append("")
        body = "\n".join(lines).rstrip() + "\n"
        with open(out, "w", encoding="utf-8") as f:
            f.write(body)
        print("wrote", out)

    # Index README in DOCS/piecemint
    index_path = os.path.join(DOCS, "README.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(
            """# Piecemint documentation mirror

This folder mirrors the `piecemint/` project tree. For each **source file** in the repo, a documentation file here explains that file’s role.

## Naming

- Doc files are named **`<original-filename>.md`** (for example `main.py.md`, `Dashboard.tsx.md`) so names stay unique in folders that contain both `App.css` and `App.tsx`.
- **Exception:** `README.md` in this tree documents the corresponding `README.md` under `piecemint/`.

## Excluded (by design)

`node_modules/`, `venv/`, `.venv/`, `dist/`, `__pycache__/`, binary blobs, and other generated or vendor content are not documented here unless explicitly listed in **`SPECS`**.

## Monorepo note

The repo root also contains **`marketplace/`** (separate product). This **`DOCS/piecemint/`** tree documents only **`piecemint/`**.

## Regenerating

Run `python3 DOCS/generate_doc_files.py` from the repository root, and extend the `SPECS` map in that script when you add new source files.

"""
        )
    print("wrote", index_path)


if __name__ == "__main__":
    main()
