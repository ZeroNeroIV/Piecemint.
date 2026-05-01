/**
 * Single-workspace app: browser storage keys are not scoped by workspace id.
 * If data exists only under legacy `*_tenant_a` or `*_tenant_b` keys from older builds, migrate once.
 */
const LEGACY_A = '_tenant_a';
const LEGACY_B = '_tenant_b';

export function getItemMigrated(newKey: string): string | null {
  if (typeof localStorage === 'undefined') return null;
  try {
    const v = localStorage.getItem(newKey);
    if (v !== null) return v;
    const fromA = localStorage.getItem(newKey + LEGACY_A);
    if (fromA !== null) {
      localStorage.setItem(newKey, fromA);
      return fromA;
    }
    const fromB = localStorage.getItem(newKey + LEGACY_B);
    if (fromB !== null) {
      localStorage.setItem(newKey, fromB);
      return fromB;
    }
  } catch {
    /* ignore */
  }
  return null;
}

export function setItemMigrated(newKey: string, value: string): void {
  if (typeof localStorage === 'undefined') return;
  try {
    localStorage.setItem(newKey, value);
  } catch (e) {
    console.error('localStorage setItem', newKey, e);
  }
}
