import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { catchError, debounceTime, of } from 'rxjs';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ESTADOS, estadoInfo } from '../../../accidentes/estado.constants';
import { EstadoAccidente } from '../../../accidentes/services/models/accidente.types';
import { SEVERIDAD_INFO, SeveridadInfo } from '../../../accidentes/severidad.constants';
import { UbicacionCatalogoApiService } from '../../../accidentes/services/ubicacion-catalogo-api.service';
import { CatalogoItem } from '../../../accidentes/services/models/accidente.types';
import { DisponibilidadUnidadApiService } from '../../../evidencia-unidad/services/disponibilidad-unidad-api.service';
import { UnidadEmergenciaResumen } from '../../../evidencia-unidad/services/models/evidencia-unidad.types';
import { SeguimientoApiService } from '../../services/seguimiento-api.service';
import { HistorialEmergenciaItem } from '../../models/seguimiento.types';

@Component({
  selector: 'app-historial-emergencias',
  standalone: true,
  imports: [ReactiveFormsModule, TablerIconComponent, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="mx-auto max-w-6xl p-8">
      <h1 class="m-0 mb-1 text-2xl font-bold text-text-primary">Historial de emergencias</h1>
      <p class="m-0 mb-6 text-sm text-text-secondary">Casos atendidos, con tiempos de respuesta y cierre.</p>

      <form [formGroup]="filtros" class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-7">
        <div class="grid gap-1.5">
          <label for="filtroPais" class="text-sm font-medium text-text-secondary">País</label>
          <select
            id="filtroPais"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="idpais"
          >
            <option [ngValue]="null">Todos</option>
            @for (p of paises(); track p.id) {
              <option [ngValue]="p.id">{{ p.nombre }}</option>
            }
          </select>
        </div>

        <div class="grid gap-1.5">
          <label for="filtroEstadoRegion" class="text-sm font-medium text-text-secondary">Estado/Región</label>
          <select
            id="filtroEstadoRegion"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="idestadoregion"
          >
            <option [ngValue]="null">Todos</option>
            @for (e of estadosRegion(); track e.id) {
              <option [ngValue]="e.id">{{ e.nombre }}</option>
            }
          </select>
        </div>

        <div class="grid gap-1.5">
          <label for="filtroSeveridad" class="text-sm font-medium text-text-secondary">Severidad</label>
          <select
            id="filtroSeveridad"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="idseveridad"
          >
            <option [ngValue]="null">Todas</option>
            @for (s of severidadOptions; track s.value) {
              <option [ngValue]="s.value">{{ s.label }}</option>
            }
          </select>
        </div>

        <div class="grid gap-1.5">
          <label for="filtroEstado" class="text-sm font-medium text-text-secondary">Estado del caso</label>
          <select
            id="filtroEstado"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="estado"
          >
            <option [ngValue]="null">Todos</option>
            @for (e of estados; track e) {
              <option [ngValue]="e">{{ estado(e).label }}</option>
            }
          </select>
        </div>

        <div class="grid gap-1.5">
          <label for="filtroUnidad" class="text-sm font-medium text-text-secondary">Unidad</label>
          <select
            id="filtroUnidad"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="idunidademergencia"
          >
            <option [ngValue]="null">Todas</option>
            @for (u of unidades(); track u.idunidademergencia) {
              <option [ngValue]="u.idunidademergencia">{{ u.nombre ?? ('Unidad #' + u.idunidademergencia) }}</option>
            }
          </select>
        </div>

        <div class="grid gap-1.5">
          <label for="filtroFechaDesde" class="text-sm font-medium text-text-secondary">Desde</label>
          <input
            id="filtroFechaDesde"
            type="date"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="fechaDesde"
          />
        </div>

        <div class="grid gap-1.5">
          <label for="filtroFechaHasta" class="text-sm font-medium text-text-secondary">Hasta</label>
          <input
            id="filtroFechaHasta"
            type="date"
            class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
            formControlName="fechaHasta"
          />
        </div>
      </form>

      @if (loading()) {
        <div class="grid gap-2" data-testid="loading-skeleton">
          @for (i of [1, 2, 3, 4]; track i) {
            <div class="h-14 animate-pulse rounded-md bg-bg-surface"></div>
          }
        </div>
      } @else if (error()) {
        <div
          class="grid place-items-center gap-3 rounded-lg border border-alert-critical bg-alert-critical-bg p-10 text-center"
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
      } @else if (!items().length) {
        <div
          class="grid place-items-center gap-3 rounded-lg border border-border-default bg-bg-surface p-10 text-center"
          data-testid="empty-state"
        >
          <app-tabler-icon name="history" [size]="32" />
          <p class="m-0 text-sm text-text-secondary">No hay casos que coincidan con estos filtros.</p>
        </div>
      } @else {
        <table class="w-full border-collapse overflow-hidden rounded-lg border border-border-default">
          <thead>
            <tr class="bg-bg-surface">
              <th class="border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary">ID</th>
              <th class="border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary">Fecha</th>
              <th class="border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary">Ubicación</th>
              <th class="border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary">Severidad</th>
              <th class="border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary">Estado</th>
              <th class="border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary">Unidad</th>
              <th
                class="border-b border-border-default px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-text-primary"
                title="R = Respuesta, T = Tránsito, A = Atención, Total = duración completa del caso, en minutos"
              >
                Tiempos (min)
              </th>
            </tr>
          </thead>
          <tbody>
            @for (h of items(); track h.idaccidente) {
              <tr class="border-b border-border-default last:border-b-0">
                <td class="px-4 py-3 text-sm font-medium text-text-primary">{{ h.idaccidente }}</td>
                <td class="whitespace-nowrap px-4 py-3 text-sm text-text-secondary">
                  {{ h.fecha | date: 'dd/MM/yyyy HH:mm' }}
                </td>
                <td class="max-w-[12rem] truncate px-4 py-3 text-sm text-text-secondary">
                  {{ h.ubicacion || '—' }}
                </td>
                <td class="px-4 py-3">
                  <span
                    class="inline-flex items-center gap-1.5 text-sm font-medium"
                    [class.text-alert-success]="severidad(h.severidad).tone === 'success'"
                    [class.text-alert-warning]="severidad(h.severidad).tone === 'warning'"
                    [class.text-alert-urgent]="severidad(h.severidad).tone === 'urgent'"
                    [class.text-alert-critical]="severidad(h.severidad).tone === 'critical'"
                  >
                    <app-tabler-icon [name]="severidad(h.severidad).icon" [size]="14" />
                    {{ severidad(h.severidad).label }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <span
                    class="inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold"
                    [class.bg-alert-success-bg]="estado(asEstado(h.estado)).tone === 'success'"
                    [class.text-alert-success]="estado(asEstado(h.estado)).tone === 'success'"
                    [class.bg-alert-warning-bg]="estado(asEstado(h.estado)).tone === 'warning'"
                    [class.text-alert-warning]="estado(asEstado(h.estado)).tone === 'warning'"
                    [class.bg-alert-urgent-bg]="estado(asEstado(h.estado)).tone === 'urgent'"
                    [class.text-alert-urgent]="estado(asEstado(h.estado)).tone === 'urgent'"
                    [class.bg-alert-info-bg]="estado(asEstado(h.estado)).tone === 'info'"
                    [class.text-alert-info]="estado(asEstado(h.estado)).tone === 'info'"
                  >
                    {{ estado(asEstado(h.estado)).label }}
                  </span>
                </td>
                <td class="px-4 py-3 text-sm text-text-secondary">{{ h.unidad_principal ?? '—' }}</td>
                <td class="whitespace-nowrap px-4 py-3 text-xs text-text-secondary">
                  <span title="Respuesta">R {{ h.tiempos.respuesta_min ?? '—' }}</span>
                  ·
                  <span title="Tránsito">T {{ h.tiempos.transito_min ?? '—' }}</span>
                  ·
                  <span title="Atención">A {{ h.tiempos.atencion_min ?? '—' }}</span>
                  ·
                  <span title="Duración total del caso">Total {{ h.tiempos.duracion_total_min ?? '—' }}</span>
                </td>
              </tr>
            }
          </tbody>
        </table>

        @if (truncado()) {
          <div class="mt-4 flex items-center justify-center">
            <button
              type="button"
              [disabled]="loadingMas()"
              class="inline-flex items-center gap-2 rounded-md border border-border-default px-4 py-2 text-sm font-medium text-text-primary hover:bg-bg-page disabled:opacity-50"
              (click)="cargarMas()"
            >
              @if (loadingMas()) {
                Cargando…
              } @else {
                Cargar más
              }
            </button>
          </div>
        }
      }
    </div>
  `,
})
export class HistorialEmergenciasPage implements OnInit {
  private readonly api = inject(SeguimientoApiService);
  private readonly ubicacionCatalogo = inject(UbicacionCatalogoApiService);
  private readonly unidadApi = inject(DisponibilidadUnidadApiService);
  private readonly fb = inject(FormBuilder);

  readonly severidadOptions = Object.entries(SEVERIDAD_INFO).map(([value, info]) => ({
    value: Number(value),
    label: info.label,
  }));
  readonly estados = ESTADOS;
  readonly estado = estadoInfo;

  readonly paises = signal<CatalogoItem[]>([]);
  readonly estadosRegion = signal<CatalogoItem[]>([]);
  readonly unidades = signal<UnidadEmergenciaResumen[]>([]);

  readonly items = signal<HistorialEmergenciaItem[]>([]);
  readonly loading = signal(false);
  readonly loadingMas = signal(false);
  readonly error = signal<string | null>(null);
  readonly truncado = signal(false);

  private nextCursor: string | null = null;

  readonly filtros = this.fb.group({
    idpais: [null as number | null],
    idestadoregion: [null as number | null],
    idseveridad: [null as number | null],
    estado: [null as string | null],
    idunidademergencia: [null as number | null],
    fechaDesde: [''],
    fechaHasta: [''],
  });

  ngOnInit(): void {
    this.cargar();
    this.ubicacionCatalogo.listarPaises().subscribe((paises) => this.paises.set(paises));
    this.unidadApi
      .listarUnidades({ limit: 100 })
      .pipe(
        // El listado completo de flota está reservado a Administrador/Despacho
        // (IsAdministradorOrDespachoService). Si el Operador no tiene acceso,
        // el filtro de Unidad simplemente queda sin opciones — no debe tronar
        // el resto de la pantalla.
        catchError(() => of({ data: { items: [] } })),
      )
      .subscribe((res) => this.unidades.set(res.data.items));

    this.filtros.controls.idpais.valueChanges.subscribe((idpais) => {
      this.filtros.controls.idestadoregion.setValue(null, { emitEvent: false });
      this.estadosRegion.set([]);
      if (idpais) {
        this.ubicacionCatalogo.listarEstados(idpais).subscribe((estados) => this.estadosRegion.set(estados));
      }
    });

    this.filtros.valueChanges.pipe(debounceTime(300)).subscribe(() => this.cargar());
  }

  severidad(idseveridad: number): SeveridadInfo {
    return (
      SEVERIDAD_INFO[idseveridad] ?? {
        value: idseveridad,
        label: `Sev. ${idseveridad}`,
        icon: 'info-circle',
        tone: 'success',
      }
    );
  }

  asEstado(estado: string): EstadoAccidente {
    return estado as EstadoAccidente;
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.nextCursor = null;
    this.buscar().subscribe({
      next: (res) => {
        this.items.set(res.data.items);
        this.nextCursor = res.data.next_cursor;
        this.truncado.set(!!this.nextCursor);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar el historial de emergencias.');
        this.loading.set(false);
      },
    });
  }

  cargarMas(): void {
    if (!this.nextCursor) {
      return;
    }
    this.loadingMas.set(true);
    this.buscar(this.nextCursor).subscribe({
      next: (res) => {
        this.items.update((actuales) => [...actuales, ...res.data.items]);
        this.nextCursor = res.data.next_cursor;
        this.truncado.set(!!this.nextCursor);
        this.loadingMas.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar más resultados.');
        this.loadingMas.set(false);
      },
    });
  }

  private buscar(cursor?: string) {
    const raw = this.filtros.getRawValue();
    return this.api.listarHistorial({
      cursor,
      limit: 20,
      estado: raw.estado ?? undefined,
      idseveridad: raw.idseveridad ?? undefined,
      idunidademergencia: raw.idunidademergencia ?? undefined,
      idestadoregion: raw.idestadoregion ?? undefined,
      fechaDesde: raw.fechaDesde ? new Date(raw.fechaDesde).getTime() : undefined,
      fechaHasta: raw.fechaHasta ? new Date(raw.fechaHasta).getTime() : undefined,
    });
  }
}
