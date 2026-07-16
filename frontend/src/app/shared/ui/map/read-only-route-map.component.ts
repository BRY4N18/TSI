import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
  inject,
} from '@angular/core';
import * as L from 'leaflet';

import { RutaService } from '../../services/ruta.service';
import { TablerIconName, tablerIconPaths } from '../icon/tabler-icon.component';

/**
 * Mismos tokens de tono usados por SEVERIDAD_INFO (accidentes/severidad.constants.ts)
 * y por el mapa de seguimiento — el design system exige que los pines reutilicen la
 * misma iconografía semántica de severidad ya definida (design-system.md §5 "Mapa").
 */
const TONE_COLOR: Record<string, string> = {
  success: 'var(--alert-success)',
  warning: 'var(--alert-warning)',
  urgent: 'var(--alert-urgent)',
  critical: 'var(--alert-critical)',
};

const UNIDAD_COLOR = 'var(--accent-primary)';

function destinoPin(color: string, iconName: TablerIconName): L.DivIcon {
  const glyphPaths = tablerIconPaths(iconName)
    .map(
      (d) =>
        `<path d="${d}" transform="translate(6.5,6.5) scale(0.46)" fill="none" stroke="${color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>`,
    )
    .join('');
  return L.divIcon({
    className: 'app-mapa-pin',
    html: `<svg width="28" height="36" viewBox="0 0 24 32" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 20 12 20s12-11 12-20c0-6.6-5.4-12-12-12z" fill="${color}"/>
      <circle cx="12" cy="12" r="8.5" fill="#ffffff"/>
      ${glyphPaths}
    </svg>`,
    iconSize: [28, 36],
    iconAnchor: [14, 34],
  });
}

function origenPin(color: string): L.DivIcon {
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
 * Mapa de solo-lectura (Leaflet + OSM) para pantallas de despacho/monitoreo: pinta
 * el destino (accidente, con icono+color de severidad) y, si hay origen, la unidad
 * más la ruta por calles reales (RutaService, fail-open a línea recta). A diferencia
 * de LocationPickerMapComponent, no es interactivo — no hay click-to-place ni drag.
 */
@Component({
  selector: 'app-read-only-route-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<div #mapContainer class="h-full w-full rounded-lg border border-border-default"></div>`,
})
export class ReadOnlyRouteMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input({ required: true }) destinoLat!: number;
  @Input({ required: true }) destinoLng!: number;
  @Input() destinoIcono: TablerIconName = 'alert-circle';
  @Input() destinoTono: keyof typeof TONE_COLOR = 'warning';
  @Input() origenLat: number | null = null;
  @Input() origenLng: number | null = null;

  @ViewChild('mapContainer', { static: true }) private readonly mapContainer!: ElementRef<HTMLDivElement>;

  private readonly rutaService = inject(RutaService);
  private map: L.Map | null = null;
  private ruta: L.Polyline | null = null;

  ngAfterViewInit(): void {
    this.map = L.map(this.mapContainer.nativeElement, { zoomControl: false }).setView(
      [this.destinoLat, this.destinoLng],
      14,
    );
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(this.map);
    L.control.zoom({ position: 'bottomright' }).addTo(this.map);

    this.pintar();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!this.map) {
      return;
    }
    if (changes['destinoLat'] || changes['destinoLng'] || changes['origenLat'] || changes['origenLng']) {
      this.pintar();
    }
  }

  ngOnDestroy(): void {
    this.map?.remove();
    this.map = null;
  }

  private pintar(): void {
    if (!this.map) {
      return;
    }
    const destino = L.latLng(this.destinoLat, this.destinoLng);
    L.marker(destino, { icon: destinoPin(TONE_COLOR[this.destinoTono] ?? 'var(--text-secondary)', this.destinoIcono) }).addTo(
      this.map,
    );

    const tieneOrigen = typeof this.origenLat === 'number' && typeof this.origenLng === 'number';
    if (!tieneOrigen) {
      this.map.setView(destino, 14);
      return;
    }

    const origen = L.latLng(this.origenLat!, this.origenLng!);
    L.marker(origen, { icon: origenPin(UNIDAD_COLOR) }).addTo(this.map);

    this.ruta?.remove();
    this.rutaService.calcularRuta(origen, destino).subscribe((puntos) => {
      this.ruta = L.polyline(puntos, { color: UNIDAD_COLOR, weight: 3 }).addTo(this.map!);
      const bounds = L.latLngBounds([origen, destino]);
      this.map!.fitBounds(bounds, { padding: [32, 32], maxZoom: 15 });
    });
  }
}
