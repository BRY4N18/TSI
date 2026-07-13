import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  OnDestroy,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import * as L from 'leaflet';

import { TablerIconComponent, TablerIconName, tablerIconPaths } from '../../../../shared/ui/icon/tabler-icon.component';
import { SEVERIDAD_INFO } from '../../../accidentes/severidad.constants';
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
  Ocupada: 'var(--alert-warning)',
  'Fuera de servicio': 'var(--text-secondary)',
};

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

@Component({
  selector: 'app-mapa-seguimiento',
  standalone: true,
  imports: [TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="mx-auto max-w-6xl p-8">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 class="m-0 mb-1 text-2xl font-bold text-text-primary">Mapa de seguimiento</h1>
          <p class="m-0 text-sm text-text-secondary">
            Accidentes activos y unidades de emergencia en tiempo real.
          </p>
        </div>
        <span class="flex items-center gap-1.5 text-xs font-medium text-text-secondary">
          <span
            class="h-2 w-2 rounded-full"
            [class.bg-alert-success]="syncStatus() === 'live'"
            [class.bg-alert-warning]="syncStatus() === 'reconnecting'"
            [class.bg-alert-critical]="syncStatus() === 'offline'"
          ></span>
          {{ syncLabel() }}
        </span>
      </div>

      @if (error()) {
        <div
          class="mb-4 grid place-items-center gap-3 rounded-lg border border-alert-critical bg-alert-critical-bg p-10 text-center"
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
      }

      <div #mapContainer class="h-[32rem] w-full rounded-lg border border-border-default"></div>

      <div class="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs text-text-secondary">
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
        <span class="mx-2 h-4 border-l border-border-default"></span>
        <span class="flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-full bg-accent-primary"></span> Unidad activa
        </span>
        <span class="flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-full bg-alert-warning"></span> Unidad ocupada
        </span>
        <span class="flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-full bg-text-secondary"></span> Fuera de servicio
        </span>
      </div>
    </div>
  `,
})
export class MapaSeguimientoPage implements AfterViewInit, OnDestroy {
  private readonly api = inject(SeguimientoApiService);
  private readonly sse = inject(SeguimientoSseService);
  private readonly destroyRef = inject(DestroyRef);

  @ViewChild('mapContainer', { static: true }) private readonly mapContainer!: ElementRef<HTMLDivElement>;

  readonly error = signal<string | null>(null);
  readonly syncStatus = signal<SyncStatus>('reconnecting');

  private map: L.Map | null = null;
  private accidenteMarkers = new Map<string, L.Marker>();
  private unidadMarkers = new Map<number, L.Marker>();
  private rutaLineas = new Map<number, L.Polyline>();
  private ultimoSnapshot: MapaSeguimientoData | null = null;

  ngAfterViewInit(): void {
    this.map = L.map(this.mapContainer.nativeElement).setView(DEFAULT_CENTER, 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(this.map);

    this.cargar();
    this.conectarSse();
  }

  private destruido = false;

  ngOnDestroy(): void {
    this.destruido = true;
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

  private readonly RECONEXION_MS = 5000;

  private conectarSse(): void {
    if (this.destruido) {
      return;
    }
    this.syncStatus.set('reconnecting');
    this.sse
      .connect()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (ev) => {
          this.syncStatus.set('live');
          if (ev.type === 'seguimiento.posicion') {
            this.actualizarPosicion(ev.data as { idunidademergencia: number; latitud: number; longitud: number });
          } else {
            // Cambios de estado/ETA: se refresca el snapshot completo — son
            // menos frecuentes que las posiciones y así se evita duplicar la
            // lógica de reconciliación de marcadores/rutas.
            this.cargar();
          }
        },
        error: () => {
          // El stream termina ante cualquier falla (red, backend, etc.). Sin
          // reintento la pantalla se queda mostrando posiciones congeladas
          // sin avisar de forma clara — inaceptable en una vista de monitoreo
          // en vivo (RNF-SEG-001). Se reintenta con backoff fijo mientras el
          // componente siga vivo.
          this.syncStatus.set('offline');
          setTimeout(() => this.conectarSse(), this.RECONEXION_MS);
        },
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
        this.rutaLineas.get(id)?.remove();
        this.rutaLineas.delete(id);
      }
    }
    for (const u of data.unidades) {
      this.pintarUnidad(u, data.accidentes_activos);
    }

    if (!this.accidenteMarkers.size && !this.unidadMarkers.size) {
      return;
    }
    const bounds = L.latLngBounds([
      ...data.accidentes_activos.map((a) => L.latLng(a.coordenadas.latitud, a.coordenadas.longitud)),
      ...data.unidades.map((u) => L.latLng(u.coordenadas.latitud, u.coordenadas.longitud)),
    ]);
    if (bounds.isValid()) {
      this.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
    }
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

    this.rutaLineas.get(u.idunidademergencia)?.remove();
    this.rutaLineas.delete(u.idunidademergencia);
    if (u.idaccidente) {
      const accidente = accidentes.find((a) => a.idaccidente === u.idaccidente);
      if (accidente) {
        const linea = L.polyline(
          [latlng, L.latLng(accidente.coordenadas.latitud, accidente.coordenadas.longitud)],
          { color: 'var(--accent-primary)', weight: 2, dashArray: '6 6' },
        ).addTo(this.map!);
        this.rutaLineas.set(u.idunidademergencia, linea);
      }
    }
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
    const linea = this.rutaLineas.get(pos.idunidademergencia);
    if (linea) {
      const puntos = linea.getLatLngs() as L.LatLng[];
      linea.setLatLngs([latlng, puntos[1]]);
    }
  }
}
