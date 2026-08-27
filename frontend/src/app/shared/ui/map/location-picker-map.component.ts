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

import { nodoPinSimple } from './map-pins';

import { crearTileLayer } from './map-tile';

export interface LatLng {
  lat: number;
  lng: number;
}

const DEFAULT_CENTER: LatLng = { lat: 19.4326, lng: -99.1332 }; // CDMX — referencia si no hay coordenadas iniciales

/** Nodo hexagonal del sistema (design-system.md §3.1). */
const PIN_ICON = nodoPinSimple('var(--accent-primary)');

/**
 * Ícono de pin en SVG inline (mismo lenguaje visual que TablerIconComponent,
 * accent-primary del design system) — evita depender de los PNG por defecto
 * de Leaflet, cuyas rutas relativas no resuelven bajo el bundler de Angular
 * (esa era la causa de que el marcador no se viera).
 */

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
  private tileLayer: L.TileLayer | null = null;
  private marker: L.Marker | null = null;

  ngAfterViewInit(): void {
    const start = this.hasValidInitialCoords() ? { lat: this.lat!, lng: this.lng! } : DEFAULT_CENTER;

    this.map = L.map(this.mapContainer.nativeElement).setView([start.lat, start.lng], 13);

    this.tileLayer = crearTileLayer().addTo(this.map);

    // `alt` y `title` no son decorativos aqui: Leaflet renderiza el marcador
    // como un elemento focusable e interactivo, y sin nombre accesible un lector
    // de pantalla solo anuncia que hay un control — no que es la ubicacion del
    // accidente ni que se puede mover. Detectado por axe (PG-UI-006).
    this.marker = L.marker([start.lat, start.lng], {
      draggable: true,
      icon: PIN_ICON,
      alt: 'Ubicacion del accidente. Arrastrable para ajustar la posicion.',
      title: 'Ubicacion del accidente. Arrastrala para ajustar la posicion.',
    }).addTo(this.map);
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
