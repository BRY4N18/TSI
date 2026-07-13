import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnDestroy,
  OnChanges,
  Output,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import * as L from 'leaflet';

export interface LatLng {
  lat: number;
  lng: number;
}

const DEFAULT_CENTER: LatLng = { lat: 19.4326, lng: -99.1332 }; // CDMX — referencia si no hay coordenadas iniciales

/**
 * Ícono de pin en SVG inline (mismo lenguaje visual que TablerIconComponent,
 * accent-primary del design system) — evita depender de los PNG por defecto
 * de Leaflet, cuyas rutas relativas no resuelven bajo el bundler de Angular
 * (esa era la causa de que el marcador no se viera).
 */
const PIN_SVG = `
  <svg width="32" height="42" viewBox="0 0 24 32" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 20 12 20s12-11 12-20c0-6.6-5.4-12-12-12z" fill="#2e6ff2"/>
    <circle cx="12" cy="12" r="5" fill="#ffffff"/>
  </svg>
`;

const PIN_ICON = L.divIcon({
  className: 'app-location-pin',
  html: PIN_SVG,
  iconSize: [32, 42],
  iconAnchor: [16, 40],
});

/**
 * Selector de coordenadas en mapa (Leaflet + OpenStreetMap, decisión documentada
 * en .specify/docs/infra/infrastructure.md §6). Reemplaza la captura manual de
 * lat/lon por click-to-place / arrastre de un pin, siguiendo la Ley de Fitts
 * del design system (objetivo grande y visible en vez de dos inputs numéricos).
 */
@Component({
  selector: 'app-location-picker-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<div #mapContainer class="h-64 w-full rounded-md border border-border-default"></div>`,
})
export class LocationPickerMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input() lat: number | null = null;
  @Input() lng: number | null = null;
  @Output() coordsChange = new EventEmitter<LatLng>();

  @ViewChild('mapContainer', { static: true }) private readonly mapContainer!: ElementRef<HTMLDivElement>;

  private map: L.Map | null = null;
  private marker: L.Marker | null = null;

  ngAfterViewInit(): void {
    const start = this.hasValidInitialCoords() ? { lat: this.lat!, lng: this.lng! } : DEFAULT_CENTER;

    this.map = L.map(this.mapContainer.nativeElement).setView([start.lat, start.lng], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(this.map);

    this.marker = L.marker([start.lat, start.lng], { draggable: true, icon: PIN_ICON }).addTo(this.map);
    this.marker.on('dragend', () => this.emitFromMarker());

    this.map.on('click', (event: L.LeafletMouseEvent) => {
      this.marker?.setLatLng(event.latlng);
      this.emitFromMarker();
    });

    if (this.hasValidInitialCoords()) {
      this.emitFromMarker();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!this.marker || !this.map) {
      return;
    }
    if ((changes['lat'] || changes['lng']) && this.hasValidInitialCoords()) {
      const next = L.latLng(this.lat!, this.lng!);
      this.marker.setLatLng(next);
      this.map.panTo(next);
    }
  }

  ngOnDestroy(): void {
    this.map?.remove();
    this.map = null;
  }

  private hasValidInitialCoords(): boolean {
    return typeof this.lat === 'number' && typeof this.lng === 'number' && (this.lat !== 0 || this.lng !== 0);
  }

  private emitFromMarker(): void {
    const position = this.marker!.getLatLng();
    this.coordsChange.emit({ lat: position.lat, lng: position.lng });
  }
}
