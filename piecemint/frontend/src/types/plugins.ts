export type InstalledPlugin = {
  id: string;
  name: string;
  description: string;
  version: string;
  /** Manifest `icon:` points at a file under the plugin folder; served by GET /api/plugin-assets/{id} */
  has_icon?: boolean;
};

export type PluginsState = {
  installed: InstalledPlugin[];
  available: InstalledPlugin[];
};
