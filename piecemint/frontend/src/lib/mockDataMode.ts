import { getItemMigrated, setItemMigrated } from './localStorageScope';

const STORAGE_KEY = 'ff_debug_mock_data_v1';

export function loadMockDataMode(): boolean {
  const raw = getItemMigrated(STORAGE_KEY);
  return raw === '1';
}

export function saveMockDataMode(enabled: boolean): void {
  setItemMigrated(STORAGE_KEY, enabled ? '1' : '0');
}
