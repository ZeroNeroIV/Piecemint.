/** Public marketing / download site (separate Vite app under `marketplace/frontend`, default port 5174). */
const u = import.meta.env.VITE_MARKETPLACE_URL;
export const MARKETPLACE_URL: string =
  typeof u === 'string' && u.length > 0 ? u.replace(/\/$/, '') : 'http://localhost:5174';
