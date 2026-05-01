/** Base URL for the Piecemint API (paths like `core/...`, `plugins/...` are appended). */
// In dev, default to same-origin `/api` so Vite can proxy (see vite.config.ts) — avoids
// "Network Error" when the backend is only reachable as 127.0.0.1 or from another LAN host.
// Set VITE_API_URL to override (e.g. production build or a remote API).
const viteUrl = import.meta.env.VITE_API_URL;
const trimmed = typeof viteUrl === 'string' ? viteUrl.trim() : '';
export const API_BASE: string =
  trimmed.length > 0
    ? trimmed
    : import.meta.env.DEV
      ? '/api'
      : 'http://localhost:8000/api';
