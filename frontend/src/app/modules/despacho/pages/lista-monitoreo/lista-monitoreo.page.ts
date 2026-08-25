import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AccidenteApiService } from '../../../accidentes/services/accidente-api.service';
import { AccidenteListItem, EstadoAccidente } from '../../../accidentes/services/models/accidente.types';
import { SEVERIDAD_INFO, SeveridadInfo } from '../../../accidentes/severidad.constants';
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
          (click)="cargar()"
        >
          <app-tabler-icon name="refresh" [size]="16" />
          Actualizar
        </button>
      </div>

      @if (truncado()) {
        <div class="mb-4 flex items-center gap-2 rounded-md border border-alert-warning bg-alert-warning-bg px-4 py-3 text-sm text-alert-warning">
          <app-tabler-icon name="alert-triangle" [size]="16" />
          Mostrando los {{ limite }} accidentes activos más recientes — puede haber más casos activos sin
          mostrar aquí. Usa los filtros de la lista de accidentes para acotar la búsqueda.
        </div>
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
      } @else {
        <ul class="m-0 grid gap-3">
          @for (a of casos(); track a.idaccidente) {
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
      }
    </div>
  `,
})
export class ListaMonitoreoPage implements OnInit {
  private readonly api = inject(AccidenteApiService);

  readonly limite = 100;

  readonly casos = signal<AccidenteListItem[]>([]);
  readonly truncado = signal(false);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly estado = estadoInfo;

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

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listar({ activo: true, limit: this.limite }).subscribe({
      next: (res) => {
        this.casos.set(res.data.filter((a) => ESTADOS_EN_DESPACHO.includes(a.estado_actual as EstadoAccidente)));
        this.truncado.set(res.data.length >= this.limite);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar la lista de despachos activos.');
        this.loading.set(false);
      },
    });
  }
}
