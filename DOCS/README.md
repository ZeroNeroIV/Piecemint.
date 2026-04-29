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

There is no mirrored doc tree under **`DOCS/`** yet for the marketplace app. See **`marketplace/frontend`** and **`marketplace/backend`** in the repo.

## Root scripts

From the repo root, **`package.json`** defines **`npm run dev`** (concurrent Piecemint + marketplace dev servers). Piecemint backend dependencies are managed with **Pipenv** in **`piecemint/backend`**.
