import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  Injector,
  OnDestroy,
  ViewChild,
  effect,
  inject,
  signal,
} from '@angular/core';
import * as L from 'leaflet';

import { TablerIconComponent, TablerIconName, tablerIconPaths } from '../../../../shared/ui/icon/tabler-icon.component';
import { SEVERIDAD_INFO } from '../../../accidentes/severidad.constants';
import { RutaService } from '../../../../shared/services/ruta.service';
import { ThemeService } from '../../../../shared/theme/theme.service';
import { crearTileLayer } from '../../../../shared/ui/map/map-tile';
import { SeguimientoApiService } from '../../services/seguimiento-api.service';
import { SeguimientoSseService } from '../../services/seguimiento-sse.service';
import { MapaSeguimientoData, MarcadorAccidente, UnidadEnMapa } from '../../models/seguimiento.types';

type SyncStatus = 'live' | 'reconnecting' | 'offline';

const DEFAULT_CENTER: L.LatLngExpression = [19.4326, -99.1332]; // CDMX — referencia si no hay marcadores

const TONE_COLOR: Record<string, string> = {
  success: 'var(--alert-success)',
  warning: 'var(--alert-warning)',
  urgent: 'var(--alert-urgent)',
  critical: 'var(--alert-critical)',
};

const UNIDAD_COLOR: Record<string, string> = {
  Activa: 'var(--accent-primary)',
  Ocupada: 'var(--text-secondary)',
  'En Misión': 'var(--alert-warning)',
  'Fuera de servicio': 'var(--text-secondary)',
};

// Umbrales de recálculo de ruta — evita llamar al motor de ruteo en cada
// ping de posición (~10s); solo se recalcula si pasó suficiente tiempo Y
// distancia desde el último cálculo de esa unidad.
const RECALCULO_MIN_MS = 30_000;
const RECALCULO_MIN_METROS = 100;

interface RutaCacheEntry {
  linea: L.Polyline;
  ultimoCalculo: number;
  origenUltimoCalculo: L.LatLng;
}

function accidentePin(color: string, iconName: TablerIconName): L.DivIcon {
  const glyphPaths = tablerIconPaths(iconName)
    .map((d) => `<path d="${d}" transform="translate(6.5,6.5) scale(0.46)" fill="none" stroke="${color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>`)
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

function unidadPin(color: string): L.DivIcon {
  return L.divIcon({
    className: 'app-mapa-pin',
    html: `<svg width="22" height="22" viewBox="0 0 22 22" xmlns="http://www.w3.org/2000/svg">
      <circle cx="11" cy="11" r="9" fill="${color}" stroke="#ffffff" stroke-width="3"/>
    </svg>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });
}

function distanciaMetros(a: L.LatLng, b: L.LatLng): number {
  return a.distanceTo(b);
}

@Component({
  selector: 'app-mapa-seguimiento',
  standalone: true,
  imports: [TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="relative h-full w-full">
      <div #mapContainer class="absolute inset-0"></div>

      <!-- Estado de sincronización — flotante arriba-derecha -->
      <div
        class="absolute right-4 top-4 z-[1000] flex items-center gap-1.5 rounded-lg border border-border-default bg-bg-surface px-3 py-1.5 text-xs font-medium text-text-secondary shadow"
      >
        <span
          class="h-2 w-2 rounded-full"
          [class.bg-alert-success]="syncStatus() === 'live'"
          [class.bg-alert-warning]="syncStatus() === 'reconnecting'"
          [class.bg-alert-critical]="syncStatus() === 'offline'"
        ></span>
        {{ syncLabel() }}
      </div>

      <!-- Leyenda — flotante abajo-izquierda -->
      <div
        class="absolute bottom-4 left-4 z-[1000] flex flex-col gap-1.5 rounded-lg border border-border-default bg-bg-surface p-3 text-xs text-text-secondary shadow"
      >
        <span class="flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-full bg-alert-critical"></span> Fatal
        </span>
        <span class="flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-full bg-alert-urgent"></span> Grave
        </span>
        <span class="flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-full bg-alert-warning"></span> Moderado
        </span>
        <span class="flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-full bg-alert-success"></span> Leve
        </span>
        <span class="my-1 border-t border-border-default"></span>
        <span class="flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-full bg-accent-primary"></span> Unidad activa
        </span>
        <span class="flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-full bg-alert-warning"></span> Unidad en misión
        </span>
        <span class="flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-full bg-text-secondary"></span> Fuera de servicio
        </span>
      </div>

      <!-- Centrar vista — flotante abajo-derecha, debajo del zoom nativo de Leaflet -->
      <button
        type="button"
        class="absolute bottom-[6.5rem] right-4 z-[1000] flex h-9 w-9 items-center justify-center rounded-md border border-border-default bg-bg-surface text-text-secondary shadow hover:bg-bg-page hover:text-text-primary"
        (click)="centrarVista()"
        aria-label="Centrar vista"
        title="Centrar vista"
      >
        <app-tabler-icon name="focus-2" [size]="18" />
      </button>

      @if (error()) {
        <div class="absolute inset-0 z-[1100] grid place-items-center bg-bg-page/70 p-8">
          <div
            class="grid place-items-center gap-3 rounded-lg border border-alert-critical bg-alert-critical-bg p-10 text-center shadow"
            data-testid="error-state"
          >
            <app-tabler-icon name="alert-triangle" [size]="32" />
            <p class="m-0 text-sm text-alert-critical">{{ error() }}</p>
            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-md border border-alert-critical px-4 py-2 text-sm font-medium text-alert-critical hover:bg-alert-critical-bg"
              (click)="cargar()"
            >
              <app-tabler-icon name="refresh" [size]="16" />
              Reintentar
            </button>
          </div>
        </div>
      }
    </div>
  `,
})
export class MapaSeguimientoPage implements AfterViewInit, OnDestroy {
  private readonly api = inject(SeguimientoApiService);
  private readonly sse = inject(SeguimientoSseService);
  private readonly rutaService = inject(RutaService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly themeService = inject(ThemeService);
  private readonly injector = inject(Injector);

  @ViewChild('mapContainer', { static: true }) private readonly mapContainer!: ElementRef<HTMLDivElement>;

  readonly error = signal<string | null>(null);
  readonly syncStatus = signal<SyncStatus>('reconnecting');

  private map: L.Map | null = null;
  private tileLayer: L.TileLayer | null = null;
  private accidenteMarkers = new Map<string, L.Marker>();
  private unidadMarkers = new Map<number, L.Marker>();
  private rutaCache = new Map<number, RutaCacheEntry>();
  private ultimoSnapshot: MapaSeguimientoData | null = null;

  ngAfterViewInit(): void {
    this.map = L.map(this.mapContainer.nativeElement, { zoomControl: false }).setView(DEFAULT_CENTER, 12);
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

    this.cargar();
    this.conectarSse();
  }

  ngOnDestroy(): void {
    this.map?.remove();
    this.map = null;
  }

  syncLabel(): string {
    return { live: 'En vivo', reconnecting: 'Conectando…', offline: 'Sin conexión en vivo' }[this.syncStatus()];
  }

  cargar(): void {
    this.error.set(null);
    this.api.obtenerMapa().subscribe({
      next: (res) => this.pintarSnapshot(res.data),
      error: () => this.error.set('No se pudo cargar el mapa de seguimiento.'),
    });
  }

  centrarVista(): void {
    if (!this.map || !this.ultimoSnapshot) {
      return;
    }
    const bounds = L.latLngBounds([
      ...this.ultimoSnapshot.accidentes_activos.map((a) => L.latLng(a.coordenadas.latitud, a.coordenadas.longitud)),
      ...this.ultimoSnapshot.unidades.map((u) => L.latLng(u.coordenadas.latitud, u.coordenadas.longitud)),
    ]);
    if (bounds.isValid()) {
      this.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
    }
  }

  private conectarSse(): void {
    // La reconexión con backoff fijo vive en SeguimientoSseService
    // (compartida con cualquier otro consumidor del stream); esta página
    // solo reacciona a los cambios de estado/eventos.
    this.sse.connectResiliente(this.destroyRef).subscribe((update) => {
      this.syncStatus.set(update.estado);
      const ev = update.evento;
      if (!ev) {
        return;
      }
      if (ev.type === 'seguimiento.posicion') {
        this.actualizarPosicion(ev.data as { idunidademergencia: number; latitud: number; longitud: number });
      } else {
        // Cambios de estado/ETA: se refresca el snapshot completo — son
        // menos frecuentes que las posiciones y así se evita duplicar la
        // lógica de reconciliación de marcadores/rutas.
        this.cargar();
      }
    });
  }

  private pintarSnapshot(data: MapaSeguimientoData): void {
    if (!this.map) {
      return;
    }
    this.ultimoSnapshot = data;

    const idsAccidentes = new Set(data.accidentes_activos.map((a) => a.idaccidente));
    for (const [id, marker] of this.accidenteMarkers) {
      if (!idsAccidentes.has(id)) {
        marker.remove();
        this.accidenteMarkers.delete(id);
      }
    }
    for (const a of data.accidentes_activos) {
      this.pintarAccidente(a);
    }

    const idsUnidades = new Set(data.unidades.map((u) => u.idunidademergencia));
    for (const [id, marker] of this.unidadMarkers) {
      if (!idsUnidades.has(id)) {
        marker.remove();
        this.unidadMarkers.delete(id);
        this.rutaCache.get(id)?.linea.remove();
        this.rutaCache.delete(id);
      }
    }
    for (const u of data.unidades) {
      this.pintarUnidad(u, data.accidentes_activos);
    }

    if (!this.accidenteMarkers.size && !this.unidadMarkers.size) {
      return;
    }
    this.centrarVista();
  }

  private pintarAccidente(a: MarcadorAccidente): void {
    const info = SEVERIDAD_INFO[a.idseveridad];
    const tone = info?.tone ?? 'info';
    const iconName: TablerIconName = info?.icon ?? 'info-circle';
    const icon = accidentePin(TONE_COLOR[tone] ?? 'var(--text-secondary)', iconName);
    const latlng = L.latLng(a.coordenadas.latitud, a.coordenadas.longitud);
    const label = info?.label ?? `Sev. ${a.idseveridad}`;

    const existing = this.accidenteMarkers.get(a.idaccidente);
    if (existing) {
      existing.setLatLng(latlng).setIcon(icon);
    } else {
      const marker = L.marker(latlng, { icon }).addTo(this.map!);
      this.accidenteMarkers.set(a.idaccidente, marker);
      marker.bindPopup(`<strong>${a.idaccidente}</strong><br>${label} — ${a.estado}`);
    }
  }

  private pintarUnidad(u: UnidadEnMapa, accidentes: MarcadorAccidente[]): void {
    const color = UNIDAD_COLOR[u.estado_unidad] ?? 'var(--text-secondary)';
    const icon = unidadPin(color);
    const latlng = L.latLng(u.coordenadas.latitud, u.coordenadas.longitud);
    const eta = u.eta_minutos != null ? `${Math.round(u.eta_minutos)} min` : null;
    const popup = `<strong>${u.unidademergencia}</strong><br>${u.estado_unidad}${eta ? ` — ETA ${eta}` : ''}`;

    const existing = this.unidadMarkers.get(u.idunidademergencia);
    if (existing) {
      existing.setLatLng(latlng).setIcon(icon).setPopupContent(popup);
    } else {
      const marker = L.marker(latlng, { icon }).addTo(this.map!);
      marker.bindPopup(popup);
      this.unidadMarkers.set(u.idunidademergencia, marker);
    }

    if (!u.idaccidente) {
      this.rutaCache.get(u.idunidademergencia)?.linea.remove();
      this.rutaCache.delete(u.idunidademergencia);
      return;
    }
    const accidente = accidentes.find((a) => a.idaccidente === u.idaccidente);
    if (!accidente) {
      return;
    }
    const destino = L.latLng(accidente.coordenadas.latitud, accidente.coordenadas.longitud);
    this.trazarRuta(u.idunidademergencia, latlng, destino);
  }

  private trazarRuta(idunidademergencia: number, origen: L.LatLng, destino: L.LatLng): void {
    this.rutaService.calcularRuta(origen, destino).subscribe((puntos) => {
      const existente = this.rutaCache.get(idunidademergencia);
      existente?.linea.remove();
      const linea = L.polyline(puntos, { color: 'var(--accent-primary)', weight: 3 }).addTo(this.map!);
      this.rutaCache.set(idunidademergencia, {
        linea,
        ultimoCalculo: Date.now(),
        origenUltimoCalculo: origen,
      });
    });
  }

  private actualizarPosicion(pos: { idunidademergencia: number; latitud: number; longitud: number }): void {
    const marker = this.unidadMarkers.get(pos.idunidademergencia);
    if (!marker) {
      // Unidad nueva que no estaba en el snapshot inicial — se resincroniza completo.
      this.cargar();
      return;
    }
    const latlng = L.latLng(pos.latitud, pos.longitud);
    marker.setLatLng(latlng);

    const unidad = this.ultimoSnapshot?.unidades.find((u) => u.idunidademergencia === pos.idunidademergencia);
    if (unidad) {
      unidad.coordenadas = { latitud: pos.latitud, longitud: pos.longitud };
    }

    const cache = this.rutaCache.get(pos.idunidademergencia);
    if (!cache) {
      return;
    }

    const tiempoTranscurrido = Date.now() - cache.ultimoCalculo;
    const distanciaRecorrida = distanciaMetros(cache.origenUltimoCalculo, latlng);
    if (tiempoTranscurrido < RECALCULO_MIN_MS || distanciaRecorrida < RECALCULO_MIN_METROS) {
      // Todavía no amerita recalcular contra el motor de ruteo — solo se
      // reajusta visualmente el extremo de la unidad en la polyline actual.
      const puntos = cache.linea.getLatLngs() as L.LatLng[];
      cache.linea.setLatLngs([latlng, puntos[puntos.length - 1]]);
      return;
    }

    if (!unidad?.idaccidente) {
      return;
    }
    const accidente = this.ultimoSnapshot?.accidentes_activos.find((a) => a.idaccidente === unidad.idaccidente);
    if (!accidente) {
      return;
    }
    this.trazarRuta(
      pos.idunidademergencia,
      latlng,
      L.latLng(accidente.coordenadas.latitud, accidente.coordenadas.longitud),
    );
  }
}
