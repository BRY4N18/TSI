import { DatePipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AccidenteApiService } from '../../../accidentes/services/accidente-api.service';
import { AccidenteListItem, EstadoAccidente } from '../../../accidentes/services/models/accidente.types';
import { SEVERIDADES, SEVERIDAD_INFO, SeveridadInfo } from '../../../accidentes/severidad.constants';
import { estadoInfo } from '../../../accidentes/estado.constants';

const ESTADOS_EN_DESPACHO: EstadoAccidente[] = ['BUSCANDO_UNIDAD', 'ASIGNADO', 'EN_ATENCIÓN'];

@Component({
  selector: 'app-lista-monitoreo',
  standalone: true,
  imports: [RouterLink, TablerIconComponent, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="mx-auto max-w-5xl p-8">
      <div class="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 class="tsi-display m-0 mb-1 text-3xl font-extrabold text-text-primary">Monitoreo de despacho</h1>
          <div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>
          <p class="m-0 text-sm text-text-secondary">Casos con búsqueda o asignación de unidad en curso.</p>
        </div>
        <button
          type="button"
          [disabled]="loading()"
          class="tsi-btn tsi-btn-secondary"
          (click)="cargar({ reiniciarCursor: true })"
        >
          <app-tabler-icon name="refresh" [size]="16" />
          Actualizar
        </button>
      </div>

      <!--
        Filtros de la propia pantalla.
        Se filtra en cliente sobre la página actual para respuesta instantánea.
      -->
      <div class="mb-4 grid gap-3 sm:grid-cols-[1fr_auto_auto]">
        <label class="grid gap-1.5">
          <span class="sr-only">Buscar por identificador o descripción</span>
          <input
            type="search"
            data-testid="filtro-texto"
            class="tsi-input w-full"
            placeholder="Buscar por identificador o descripción…"
            [value]="filtroTexto()"
            (input)="onFiltroTexto($event)"
          />
        </label>
        <label class="grid gap-1.5">
          <span class="sr-only">Filtrar por estado</span>
          <select
            data-testid="filtro-estado"
            class="tsi-select w-full min-w-0"
            [value]="filtroEstado()"
            (change)="onFiltroEstado($event)"
          >
            <option value="">Todos los estados</option>
            @for (e of estadosDisponibles; track e) {
              <option [value]="e">{{ estado(e).label }}</option>
            }
          </select>
        </label>
        <label class="grid gap-1.5">
          <span class="sr-only">Filtrar por severidad</span>
          <select
            data-testid="filtro-severidad"
            class="tsi-select w-full min-w-0"
            [value]="filtroSeveridad()"
            (change)="onFiltroSeveridad($event)"
          >
            <option value="">Todas las severidades</option>
            @for (s of severidadesDisponibles; track s.value) {
              <option [value]="s.value">{{ s.label }}</option>
            }
          </select>
        </label>
      </div>

      @if (hayFiltroActivo()) {
        <p class="mb-3 flex flex-wrap items-center gap-2 text-sm text-text-secondary">
          <span data-testid="conteo-filtrado">
            {{ casosFiltrados().length }} de {{ casos().length }} casos
          </span>
          <button type="button" class="tsi-btn tsi-btn-secondary" (click)="limpiarFiltros()">
            Limpiar filtros
          </button>
        </p>
      }

      @if (loading()) {
        <div class="grid gap-2" data-testid="loading-skeleton">
          @for (i of [1, 2, 3]; track i) {
            <div class="h-14 animate-pulse rounded-md bg-bg-surface"></div>
          }
        </div>
      } @else if (error()) {
        <div
          class="grid place-items-center gap-3 rounded-md border border-alert-critical bg-alert-critical-bg p-10 text-center"
          data-testid="error-state"
        >
          <app-tabler-icon name="alert-triangle" [size]="32" />
          <p class="m-0 text-sm text-alert-critical">{{ error() }}</p>
          <button
            type="button"
            class="tsi-btn border border-alert-critical bg-transparent text-alert-critical hover:bg-alert-critical-bg"
            (click)="cargar()"
          >
            <app-tabler-icon name="refresh" [size]="16" />
            Reintentar
          </button>
        </div>
      } @else if (!casos().length) {
        <div
          class="grid place-items-center gap-3 tsi-panel p-10 text-center"
          data-testid="empty-state"
        >
          <app-tabler-icon name="radio" [size]="32" />
          <p class="m-0 text-sm text-text-secondary">No hay casos en despacho activo en este momento.</p>
        </div>
      } @else if (!casosFiltrados().length) {
        <!-- Vacío por filtro, no por ausencia de casos -->
        <div
          class="grid place-items-center gap-3 tsi-panel p-10 text-center"
          data-testid="empty-filtro-state"
        >
          <app-tabler-icon name="search" [size]="32" />
          <p class="m-0 text-sm text-text-secondary">
            Ningún caso activo coincide con los filtros.
          </p>
          <button type="button" class="tsi-btn tsi-btn-secondary" (click)="limpiarFiltros()">
            Limpiar filtros
          </button>
        </div>
      } @else {
        <ul class="m-0 grid gap-3">
          @for (a of casosFiltrados(); track a.idaccidente) {
            <li>
              <a
                [routerLink]="['/despacho/monitoreo', a.idaccidente]"
                class="flex items-center justify-between gap-4 tsi-panel p-4 hover:border-accent-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
              >
                <div class="grid gap-1">
                  <span class="text-sm font-semibold text-text-primary">{{ a.idaccidente }}</span>
                  <span class="max-w-md truncate text-sm text-text-secondary">{{ a.descripcion }}</span>
                  <span class="text-xs text-text-secondary">
                    {{ a.fechahoraaccidente | date: 'dd/MM/yyyy HH:mm' }}
                  </span>
                </div>
                <div class="flex items-center gap-2">
                  <span
                    class="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-semibold"
                    [class.text-alert-success]="severidad(a.idseveridad).tone === 'success'"
                    [class.text-alert-warning]="severidad(a.idseveridad).tone === 'warning'"
                    [class.text-alert-urgent]="severidad(a.idseveridad).tone === 'urgent'"
                    [class.text-alert-critical]="severidad(a.idseveridad).tone === 'critical'"
                  >
                    <app-tabler-icon [name]="severidad(a.idseveridad).icon" [size]="14" />
                    {{ severidad(a.idseveridad).label }}
                  </span>
                  <span
                    class="inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold"
                    [class.bg-alert-success-bg]="estado(a.estado_actual).tone === 'success'"
                    [class.text-alert-success]="estado(a.estado_actual).tone === 'success'"
                    [class.bg-alert-warning-bg]="estado(a.estado_actual).tone === 'warning'"
                    [class.text-alert-warning]="estado(a.estado_actual).tone === 'warning'"
                    [class.bg-alert-urgent-bg]="estado(a.estado_actual).tone === 'urgent'"
                    [class.text-alert-urgent]="estado(a.estado_actual).tone === 'urgent'"
                    [class.bg-alert-info-bg]="estado(a.estado_actual).tone === 'info'"
                    [class.text-alert-info]="estado(a.estado_actual).tone === 'info'"
                  >
                    {{ estado(a.estado_actual).label }}
                  </span>
                  <app-tabler-icon name="eye" [size]="18" />
                </div>
              </a>
            </li>
          }
        </ul>

        <div
          class="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border-default px-4 py-3"
          data-testid="lista-monitoreo-pager"
        >
          <p class="m-0 text-xs text-text-secondary">
            {{ casosFiltrados().length }} de hasta {{ pageLimit }} en esta página
          </p>
          <div class="flex gap-2">
            <button
              type="button"
              data-testid="btn-pagina-anterior"
              class="tsi-btn tsi-btn-secondary"
              [disabled]="!puedeAnterior"
              (click)="paginaAnterior()"
            >
              Anterior
            </button>
            <button
              type="button"
              data-testid="btn-pagina-siguiente"
              class="tsi-btn tsi-btn-primary"
              [disabled]="!puedeSiguiente"
              (click)="paginaSiguiente()"
            >
              Siguiente
            </button>
          </div>
        </div>
      }
    </div>
  `,
})
export class ListaMonitoreoPage implements OnInit {
  private readonly api = inject(AccidenteApiService);

  readonly pageLimit = 20;
  readonly nextCursor = signal<string | null>(null);
  cursor: string | null = null;
  private cursorStack: (string | null)[] = [];

  readonly casos = signal<AccidenteListItem[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly estado = estadoInfo;
  readonly estadosDisponibles = ESTADOS_EN_DESPACHO;
  readonly severidadesDisponibles = SEVERIDADES;

  readonly filtroTexto = signal('');
  readonly filtroEstado = signal('');
  readonly filtroSeveridad = signal('');

  readonly casosFiltrados = computed(() => {
    const texto = this.filtroTexto().trim().toLowerCase();
    const estadoSel = this.filtroEstado();
    const severidadSel = this.filtroSeveridad();
    return this.casos().filter((a) => {
      if (estadoSel && a.estado_actual !== estadoSel) {
        return false;
      }
      if (severidadSel && String(a.idseveridad) !== severidadSel) {
        return false;
      }
      if (!texto) {
        return true;
      }
      const id = String(a.idaccidente ?? '').toLowerCase();
      const descripcion = String(a.descripcion ?? '').toLowerCase();
      return id.includes(texto) || descripcion.includes(texto);
    });
  });

  readonly hayFiltroActivo = computed(
    () => !!(this.filtroTexto().trim() || this.filtroEstado() || this.filtroSeveridad()),
  );

  get puedeSiguiente(): boolean {
    return this.nextCursor() !== null;
  }

  get puedeAnterior(): boolean {
    return this.cursorStack.length > 0;
  }

  paginaSiguiente(): void {
    const siguiente = this.nextCursor();
    if (!siguiente) {
      return;
    }
    this.cursorStack.push(this.cursor);
    this.cursor = siguiente;
    this.cargar();
  }

  paginaAnterior(): void {
    if (!this.cursorStack.length) {
      return;
    }
    this.cursor = this.cursorStack.pop() ?? null;
    this.cargar();
  }

  onFiltroTexto(event: Event): void {
    this.filtroTexto.set((event.target as HTMLInputElement).value);
  }

  onFiltroEstado(event: Event): void {
    this.filtroEstado.set((event.target as HTMLSelectElement).value);
  }

  onFiltroSeveridad(event: Event): void {
    this.filtroSeveridad.set((event.target as HTMLSelectElement).value);
  }

  limpiarFiltros(): void {
    this.filtroTexto.set('');
    this.filtroEstado.set('');
    this.filtroSeveridad.set('');
  }

  ngOnInit(): void {
    this.cargar();
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

  cargar(opciones: { reiniciarCursor?: boolean } = {}): void {
    if (opciones.reiniciarCursor) {
      this.cursor = null;
      this.cursorStack = [];
    }
    this.loading.set(true);
    this.error.set(null);
    this.api
      .listar({
        activo: true,
        limit: this.pageLimit,
        cursor: this.cursor,
      })
      .subscribe({
        next: (res) => {
          this.casos.set(
            res.data.filter((a) =>
              ESTADOS_EN_DESPACHO.includes(a.estado_actual as EstadoAccidente),
            ),
          );
          const siguiente = res.meta?.pagination?.next_cursor;
          this.nextCursor.set(siguiente ? String(siguiente) : null);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('No se pudo cargar la lista de despachos activos.');
          this.loading.set(false);
        },
      });
  }
}
