import * as L from 'leaflet';

/**
 * Tiles claros de OpenStreetMap — único tema soportado (design-system.md §3, v9:
 * el sistema pasa a modo claro únicamente).
 */
export const LIGHT_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
export const LIGHT_TILE_ATTRIBUTION = '&copy; OpenStreetMap contributors';

export function crearTileLayer(): L.TileLayer {
  return L.tileLayer(LIGHT_TILE_URL, { attribution: LIGHT_TILE_ATTRIBUTION, maxZoom: 19 });
}
