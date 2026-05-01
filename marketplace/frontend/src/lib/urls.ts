/** Piecemint web app (Vite dev default 5173). */
const main = import.meta.env.VITE_MAIN_APP_URL;
export const MAIN_APP_URL: string =
  typeof main === 'string' && main.length > 0 ? main.replace(/\/$/, '') : 'http://127.0.0.1:5173';

/** True when hitting the marketplace API via loopback URL (often breaks in browsers: localhost → IPv6(::1)). */
function isLoopbackHostname(hostname: string): boolean {
  return (
    hostname === 'localhost' ||
    hostname === '127.0.0.1' ||
    hostname === '[::1]' ||
    hostname === '::1'
  );
}

/**
 * Marketplace catalog API URL resolution.
 *
 * In **development**, we prefer same-origin paths (`/api/...`) so Vite proxies to
 * `http://127.0.0.1:8001`. Absolute loopback URLs in `VITE_MARKETPLACE_API_URL` bypass
 * the proxy and often fail (IPv6 localhost vs IPv4 uvicorn bind).
 *
 * In **production**, an explicit `VITE_MARKETPLACE_API_URL` is honored (HTTPS remote APIs, etc.).
 *
 * If the env base is **`/api`** (or **`…/api`**) while call sites pass paths from the site root
 * (**`/api/plugins`**, …), concatenation would wrongly yield **`/api/api/...`**; that case is folded
 * back to **`/api/...`** (or **`origin…/api/...`**).
 */
const apiRaw = import.meta.env.VITE_MARKETPLACE_API_URL;

function joinMarketplaceApiBase(normalizedBase: string, absoluteFromRoot: string): string {
  const base = normalizedBase.replace(/\/$/, '');
  if (
    absoluteFromRoot.startsWith('/api/') &&
    (base === '/api' || base.endsWith('/api'))
  ) {
    const originPrefix = base === '/api' ? '' : base.slice(0, -'/api'.length);
    return `${originPrefix}${absoluteFromRoot}`;
  }
  return `${base}${absoluteFromRoot}`;
}

function marketplaceApiUsesDevProxy(): boolean {
  if (!import.meta.env.DEV) return false;
  const trimmed = typeof apiRaw === 'string' ? apiRaw.trim() : '';
  if (trimmed === '' || trimmed === '/api') return true;
  try {
    const withProto = trimmed.includes('://') ? trimmed : `http://${trimmed}`;
    const { hostname } = new URL(withProto);
    return isLoopbackHostname(hostname);
  } catch {
    return trimmed.startsWith('/');
  }
}

export function marketplaceApiPath(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`;
  if (marketplaceApiUsesDevProxy()) {
    return p;
  }
  const api = typeof apiRaw === 'string' ? apiRaw.trim() : '';
  if (api.length > 0) {
    return joinMarketplaceApiBase(api, p);
  }
  return p;
}

/** GET /api/plugins/{pluginId}/icon — same file as Piecemint /api/plugin-assets/{id}. */
export function marketplacePluginIconUrl(pluginId: string): string {
  return marketplaceApiPath(`/api/plugins/${encodeURIComponent(pluginId)}/icon`);
}
