/** Piecemint web app (Vite dev default 5173). */
const main = import.meta.env.VITE_MAIN_APP_URL;
export const MAIN_APP_URL: string =
  typeof main === 'string' && main.length > 0 ? main.replace(/\/$/, '') : 'http://localhost:5173';

/**
 * Marketplace catalog API. Empty string = same origin (use Vite proxy in dev: `/api` → backend).
 * In production, set e.g. `VITE_MARKETPLACE_API_URL=https://api.marketplace.example`.
 */
const api = import.meta.env.VITE_MARKETPLACE_API_URL;
export function marketplaceApiPath(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`;
  if (typeof api === 'string' && api.length > 0) {
    return `${api.replace(/\/$/, '')}${p}`;
  }
  return p;
}
