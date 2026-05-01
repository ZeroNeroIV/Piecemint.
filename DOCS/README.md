# DOCS

Generated and hand-written documentation for this monorepo.

## Piecemint (`piecemint/`)

- **Per-file mirror:** [`piecemint/README.md`](piecemint/README.md) — explains the naming scheme.
- **Regenerate** after adding or renaming documented files:

  ```bash
  python3 DOCS/generate_doc_files.py
  ```

  Then add a new entry to the **`SPECS`** dict in [`generate_doc_files.py`](generate_doc_files.py).

## Marketplace (`marketplace/`)

There is no mirrored doc tree under **`DOCS/`** for the marketplace app. The public **Build your own plugin** guide lives in **`marketplace/frontend/src/ForDevelopers.tsx`** (aligned with Piecemint’s in-app **`piecemint/frontend/src/pages/PluginDocsPage.tsx`** at **`/docs/plugins`**).

## Root scripts

From the repo root, **`package.json`** defines **`npm run dev`** (concurrent Piecemint + marketplace dev servers). Piecemint backend dependencies are managed with **Pipenv** in **`piecemint/backend`**; the marketplace API uses **`marketplace/backend/requirements.txt`** (run **`npm run marketplace-be-install-packages`** once, then **`npm run marketplace-be`**).
