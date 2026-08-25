import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  Input,
  OnChanges,
  Injector,
  OnDestroy,
  SimpleChanges,
  ViewChild,
  effect,
  inject,
} from '@angular/core';
import * as L from 'leaflet';

import { RutaService } from '../../services/ruta.service';
import { ThemeService } from '../../theme/theme.service';
import { TablerIconName } from '../icon/tabler-icon.component';
import { capasDeRuta, nodoPin, unidadPin } from './map-pins';
import { crearTileLayer } from './map-tile';

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
  template: `<div #mapContainer class="h-full w-full rounded-md border border-border-default"></div>`,
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
  private readonly themeService = inject(ThemeService);
  private readonly injector = inject(Injector);
  private map: L.Map | null = null;
  private ruta?: L.LayerGroup;
  private tileLayer: L.TileLayer | null = null;

  ngAfterViewInit(): void {
    this.map = L.map(this.mapContainer.nativeElement, { zoomControl: false }).setView(
      [this.destinoLat, this.destinoLng],
      14,
    );
    this.tileLayer = crearTileLayer(this.themeService.isDark()).addTo(this.map);
    L.control.zoom({ position: 'bottomright' }).addTo(this.map);

    effect(
      () => {
        const isDark = this.themeService.isDark();
        if (!this.map) {
          return;
        }
        this.tileLayer?.remove();
        this.tileLayer = crearTileLayer(isDark).addTo(this.map);
      },
      { injector: this.injector },
    );

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
    L.marker(destino, { icon: nodoPin(TONE_COLOR[this.destinoTono] ?? 'var(--text-secondary)', this.destinoIcono) }).addTo(
      this.map,
    );

    const tieneOrigen = typeof this.origenLat === 'number' && typeof this.origenLng === 'number';
    if (!tieneOrigen) {
      this.map.setView(destino, 14);
      return;
    }

    const origen = L.latLng(this.origenLat!, this.origenLng!);
    L.marker(origen, { icon: unidadPin(UNIDAD_COLOR) }).addTo(this.map);

    this.ruta?.remove();
    this.rutaService.calcularRuta(origen, destino).subscribe((puntos) => {
      // La ruta se pinta como el riel de §3.1: via + divisoria interior. Las
      // dos capas se guardan juntas para poder retirarlas a la vez.
      const [via, divisoria] = capasDeRuta(puntos);
      via.addTo(this.map!);
      divisoria.addTo(this.map!);
      this.ruta = L.layerGroup([via, divisoria]);
      const bounds = L.latLngBounds([origen, destino]);
      this.map!.fitBounds(bounds, { padding: [32, 32], maxZoom: 15 });
    });
  }
}
