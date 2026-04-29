import { API_BASE } from './apiBase';

/** Origin for non-`/api/...` paths (plugin static assets). */
export function apiOrigin(): string {
  const b = API_BASE.replace(/\/$/, '');
  if (b.endsWith('/api')) return b.slice(0, -4);
  return b;
}

/** GET /api/plugin-assets/{pluginId} — image from manifest `icon:` on the Piecemint API. */
export function piecemintPluginIconUrl(pluginId: string): string {
  return `${apiOrigin()}/api/plugin-assets/${encodeURIComponent(pluginId)}`;
}
