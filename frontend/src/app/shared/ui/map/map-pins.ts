import * as L from 'leaflet';

import { TablerIconName, tablerIconPaths } from '../icon/tabler-icon.component';

/**
 * Pines y trazos de mapa del sistema (design-system.md §3.1 y §5 "Mapa").
 *
 * Vivían duplicados casi letra por letra en `read-only-route-map.component.ts` y
 * en `mapa-seguimiento.page.ts`, más una tercera variante en
 * `location-picker-map.component.ts`. Aquí hay una sola definición.
 *
 * **Por qué hexágono y no la gota de siempre.** El hexágono es el nodo donde
 * convergen las tres vías del isotipo: un pin hexagonal *es* la marca, no un
 * adorno pegado encima, y de paso separa a TSI de la gota genérica de cualquier
 * mapa. La punta inferior sigue siendo el punto de anclaje exacto, así que no se
 * pierde nada de la precisión que da la gota.
 *
 * El color y el ícono de dentro siguen siendo los tokens semánticos de severidad
 * (§5): la forma es de marca, el color es información.
 */

/** Vértices del hexágono vertical de §3.1, en el viewBox 24x32 del pin. */
const HEX_EXTERIOR = 'M12 0 L24 8 L24 24 L12 32 L0 24 L0 8 Z';

/** El mismo hexágono inset ~3.5u: el hueco blanco donde respira el ícono. */
const HEX_INTERIOR = 'M12 4 L20.5 9.7 L20.5 22.3 L12 28 L3.5 22.3 L3.5 9.7 Z';

/**
 * Pin de nodo: hexágono de marca + ícono semántico dentro. Para accidentes y
 * destinos, donde el color comunica severidad.
 */
export function nodoPin(color: string, iconName: TablerIconName): L.DivIcon {
  // El glifo Tabler es 24x24; a escala 0.46 mide 11.04u y hay que centrarlo en
  // (12, 16), que es el centro del hexágono interior — no en (12, 12) como en
  // la gota, cuyo círculo estaba más arriba.
  const glyph = tablerIconPaths(iconName)
    .map(
      (d) =>
        `<path d="${d}" transform="translate(6.5,10.5) scale(0.46)" fill="none" ` +
        `stroke="${color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>`,
    )
    .join('');

  return L.divIcon({
    className: 'app-mapa-pin',
    html: `<svg width="30" height="40" viewBox="0 0 24 32" xmlns="http://www.w3.org/2000/svg">
      <path d="${HEX_EXTERIOR}" fill="${color}"/>
      <path d="${HEX_INTERIOR}" fill="#ffffff"/>
      ${glyph}
    </svg>`,
    iconSize: [30, 40],
    iconAnchor: [15, 40],
  });
}

/** Pin de nodo sin ícono, para elegir una ubicación (no hay severidad todavía). */
export function nodoPinSimple(color: string): L.DivIcon {
  return L.divIcon({
    className: 'app-location-pin',
    html: `<svg width="30" height="40" viewBox="0 0 24 32" xmlns="http://www.w3.org/2000/svg">
      <path d="${HEX_EXTERIOR}" fill="${color}"/>
      <path d="${HEX_INTERIOR}" fill="#ffffff"/>
    </svg>`,
    iconSize: [30, 40],
    iconAnchor: [15, 40],
  });
}

/**
 * Marcador de unidad: círculo, no hexágono. La distinción es deliberada — el
 * hexágono es el nodo (un punto fijo del mapa) y la unidad es lo que se mueve
 * por las vías hacia él. Darles la misma forma borraría esa lectura.
 */
export function unidadPin(color: string): L.DivIcon {
  return L.divIcon({
    className: 'app-mapa-pin',
    html: `<svg width="22" height="22" viewBox="0 0 22 22" xmlns="http://www.w3.org/2000/svg">
      <circle cx="11" cy="11" r="9" fill="${color}" stroke="#ffffff" stroke-width="3"/>
    </svg>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });
}

/**
 * La ruta hacia un caso activo dibujada como **el riel** de §3.1: trazo grueso
 * en `accent-flow` con una divisoria fina corriendo por dentro. Es la misma
 * construcción del isotipo — vía + línea divisoria — sobre un mapa real, y es
 * el trabajo que §3.1 le asigna al cian: flujo en curso, no severidad.
 *
 * Se devuelven dos capas porque una polilínea no puede llevar su propia
 * divisoria; hay que superponerlas y añadirlas en orden.
 */
export function capasDeRuta(puntos: L.LatLngExpression[]): [L.Polyline, L.Polyline] {
  const via = L.polyline(puntos, {
    color: 'var(--accent-flow)',
    weight: 7,
    lineJoin: 'round',
    lineCap: 'round',
  });
  const divisoria = L.polyline(puntos, {
    color: 'var(--rail-groove)',
    weight: 1.5,
    lineJoin: 'round',
    lineCap: 'round',
  });
  return [via, divisoria];
}
