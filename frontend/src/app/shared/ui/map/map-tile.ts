import * as L from 'leaflet';

/**
 * Tiles claros/oscuros para que el mapa (Leaflet) respete el tema activo — sin esto,
 * el mapa se queda claro aunque el resto de la interfaz cambie a oscuro (design-system.md §3).
 * CartoDB Dark Matter: mismo proveedor gratuito sin API key que OSM, solo cambia el estilo.
 */
export const LIGHT_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
export const LIGHT_TILE_ATTRIBUTION = '&copy; OpenStreetMap contributors';

export const DARK_TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
export const DARK_TILE_ATTRIBUTION = '&copy; OpenStreetMap contributors &copy; CARTO';

export function crearTileLayer(isDark: boolean): L.TileLayer {
  return isDark
    ? L.tileLayer(DARK_TILE_URL, { attribution: DARK_TILE_ATTRIBUTION, maxZoom: 19 })
    : L.tileLayer(LIGHT_TILE_URL, { attribution: LIGHT_TILE_ATTRIBUTION, maxZoom: 19 });
}
