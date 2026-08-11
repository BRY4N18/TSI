import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../shared/ui/list-states/list-table.styles';
import { MonitoreoApiService } from '../../services/monitoreo-api.service';
import { PartnerApiService } from '../../services/partner-api.service';
import { variacionPorcentual } from '../../services/models/monitoreo.types';
import type { ReporteMensual } from '../../services/models/monitoreo.types';
import type { PartnerListItem } from '../../services/models/partner.types';

/**
 * Reporte mensual de consumo (RF-APM-009).
 *
 * Dos cosas que esta pantalla trata con cuidado:
 *
 * 1. **Un mes sin llamadas devuelve ceros, y eso NO es un error.** El backend lo
 *    dice explícitamente: es el caso límite normal de una agregación sobre
 *    conjunto vacío. Pintarlo con el vacío gris de un fallo de red convertiría
 *    una respuesta correcta en una sospecha de avería.
 * 2. **La variación contra un período de 0 llamadas no existe.** No es
 *    «+100 %» ni «Infinity»: es «sin base de comparación».
 *
 * El período viaja en la URL para que un reporte se pueda compartir por enlace
 * y sobreviva a un refresco.
 */
@Component({
  selector: 'app-reporte-consumo',
  standalone: true,
  imports: [
    FormsModule,
    ListEmptyStateComponent,
    ListErrorStateComponent,
    ListLoadingSkeletonComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <h1 class="m-0 text-2xl font-bold text-text-primary">Reporte mensual de consumo</h1>
      <p class="mt-1 text-sm text-text-secondary" data-testid="leyenda-entorno">
        Este reporte incluye únicamente consumo de <strong>producción</strong>.
      </p>

      <div class="mt-4 flex flex-wrap items-end gap-4 rounded-lg border border-border-default bg-bg-surface p-4">
        <label class="flex flex-col gap-1 text-sm">
          <span class="text-xs uppercase tracking-wide text-text-secondary">Partner</span>
          <select
            class="rounded-lg border border-border-default bg-bg-surface px-3 py-2 text-sm"
            [ngModel]="idpartner()"
            (ngModelChange)="idpartner.set($event)"
            data-testid="select-partner"
          >
            <option [ngValue]="null">Elige un partner…</option>
            @for (p of partners(); track p.idpartner) {
              <option [ngValue]="p.idpartner">{{ p.nombrepartner }}</option>
            }
          </select>
        </label>
        <label class="flex flex-col gap-1 text-sm">
          <span class="text-xs uppercase tracking-wide text-text-secondary">Año</span>
          <input
            type="number"
            class="w-24 rounded-lg border border-border-default bg-bg-surface px-3 py-2 text-sm"
            [ngModel]="anio()"
            (ngModelChange)="anio.set(+$event)"
            data-testid="input-anio"
          />
        </label>
        <label class="flex flex-col gap-1 text-sm">
          <span class="text-xs uppercase tracking-wide text-text-secondary">Mes</span>
          <input
            type="number"
            min="1"
            max="12"
            class="w-20 rounded-lg border border-border-default bg-bg-surface px-3 py-2 text-sm"
            [ngModel]="mes()"
            (ngModelChange)="mes.set(+$event)"
            data-testid="input-mes"
          />
        </label>
        <label class="flex items-center gap-2 text-sm text-text-secondary">
          <input
            type="checkbox"
            [ngModel]="comparar()"
            (ngModelChange)="comparar.set($event)"
            data-testid="chk-comparar"
          />
          Comparar con otro período
        </label>
        @if (comparar()) {
          <label class="flex flex-col gap-1 text-sm">
            <span class="text-xs uppercase tracking-wide text-text-secondary">Año a comparar</span>
            <input
              type="number"
              class="w-24 rounded-lg border border-border-default bg-bg-surface px-3 py-2 text-sm"
              [ngModel]="anioComparar()"
              (ngModelChange)="anioComparar.set(+$event)"
              data-testid="input-anio-comparar"
            />
          </label>
          <label class="flex flex-col gap-1 text-sm">
            <span class="text-xs uppercase tracking-wide text-text-secondary">Mes a comparar</span>
            <input
              type="number"
              min="1"
              max="12"
              class="w-20 rounded-lg border border-border-default bg-bg-surface px-3 py-2 text-sm"
              [ngModel]="mesComparar()"
              (ngModelChange)="mesComparar.set(+$event)"
              data-testid="input-mes-comparar"
            />
          </label>
        }
        <button
          type="button"
          class="rounded-lg bg-accent-primary px-4 py-2 text-sm font-medium text-white"
          (click)="consultar()"
          data-testid="btn-consultar"
        >
          Consultar
        </button>
      </div>

      @if (idpartner() === null) {
        <app-list-empty-state message="Elige un partner para ver su reporte." icon="filter" />
      } @else if (cargando()) {
        <app-list-loading-skeleton [count]="3" />
      } @else if (error()) {
        <app-list-error-state [message]="error()!" (retry)="consultar()" />
      } @else {
        @if (reporte(); as r) {
          @if (r.llamadas === 0) {
            <!-- Ceros NO son un error: es el caso límite normal (RF-APM-009). -->
            <app-list-empty-state
              message="Este período no registró consumo. No es un error: el partner no realizó llamadas en producción."
              icon="list"
            />
          } @else {
            <div class="mt-4 grid gap-4 sm:grid-cols-3">
              <div class="rounded-lg border border-border-default bg-bg-surface p-6">
                <p class="m-0 text-xs uppercase tracking-wide text-text-secondary">Llamadas</p>
                <p class="m-0 mt-1 font-mono text-xl text-text-primary" data-testid="kpi-llamadas">
                  {{ r.llamadas.toLocaleString('es-EC') }}
                </p>
                <!-- Se condiciona al TEXTO, no al porcentaje: cuando no hay
                     base de comparación el porcentaje es null y aun así hay
                     algo que decir («sin base de comparación»). -->
                @if (textoVariacion()) {
                  <p class="m-0 mt-1 text-xs text-text-secondary" data-testid="variacion">
                    {{ textoVariacion() }}
                  </p>
                }
              </div>
              <div class="rounded-lg border border-border-default bg-bg-surface p-6">
                <p class="m-0 text-xs uppercase tracking-wide text-text-secondary">Errores</p>
                <p class="m-0 mt-1 font-mono text-xl text-text-primary" data-testid="kpi-errores">
                  {{ r.errores.toLocaleString('es-EC') }}
                </p>
              </div>
              <div class="rounded-lg border border-border-default bg-bg-surface p-6">
                <p class="m-0 text-xs uppercase tracking-wide text-text-secondary">
                  Latencia media
                </p>
                <p class="m-0 mt-1 font-mono text-xl text-text-primary" data-testid="kpi-latencia">
                  {{ r.latencia_media_ms }} ms
                </p>
              </div>
            </div>
          }
        }
      }
    </section>
  `,
})
export class ReporteConsumoPage implements OnInit {
  private readonly monitoreo = inject(MonitoreoApiService);
  private readonly partnersApi = inject(PartnerApiService);
  private readonly ruta = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;

  readonly partners = signal<PartnerListItem[]>([]);
  readonly idpartner = signal<number | null>(null);
  readonly anio = signal(new Date().getFullYear());
  readonly mes = signal(new Date().getMonth() + 1);
  readonly comparar = signal(false);
  readonly anioComparar = signal(new Date().getFullYear());
  readonly mesComparar = signal(1);

  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);
  readonly reporte = signal<ReporteMensual | null>(null);
  readonly reporteComparado = signal<ReporteMensual | null>(null);
  readonly variacion = signal<number | null>(null);
  readonly textoVariacion = signal('');

  ngOnInit(): void {
    // El período viaja en la URL: un reporte debe poder compartirse por enlace.
    const q = this.ruta.snapshot.queryParamMap;
    if (q.get('idpartner')) {
      this.idpartner.set(Number(q.get('idpartner')));
    }
    if (q.get('anio')) {
      this.anio.set(Number(q.get('anio')));
    }
    if (q.get('mes')) {
      this.mes.set(Number(q.get('mes')));
    }

    this.partnersApi.listar({ limit: 100 }).subscribe({
      next: ({ data }) => this.partners.set(data ?? []),
      error: () => this.partners.set([]),
    });

    if (this.idpartner() !== null) {
      this.consultar();
    }
  }

  consultar(): void {
    const id = this.idpartner();
    if (id === null) {
      return;
    }
    this.cargando.set(true);
    this.error.set(null);
    this.variacion.set(null);
    this.textoVariacion.set('');

    void this.router.navigate([], {
      relativeTo: this.ruta,
      queryParams: { idpartner: id, anio: this.anio(), mes: this.mes() },
      queryParamsHandling: 'merge',
    });

    this.monitoreo.reporteMensual(id, this.anio(), this.mes()).subscribe({
      next: ({ data }) => {
        this.reporte.set(data);
        this.cargando.set(false);
        if (this.comparar()) {
          this.cargarComparacion(id, data);
        }
      },
      error: (err: { status?: number }) => {
        this.error.set(
          err?.status === 403
            ? 'No tienes acceso a esta información.'
            : 'No se pudo cargar el reporte.',
        );
        this.cargando.set(false);
      },
    });
  }

  private cargarComparacion(id: number, actual: ReporteMensual): void {
    this.monitoreo.reporteMensual(id, this.anioComparar(), this.mesComparar()).subscribe({
      next: ({ data }) => {
        this.reporteComparado.set(data);
        const v = variacionPorcentual(actual.llamadas, data.llamadas);
        this.variacion.set(v.valor);
        const absoluta = actual.llamadas - data.llamadas;
        this.textoVariacion.set(
          v.valor === null
            ? `${absoluta >= 0 ? '+' : ''}${absoluta} llamadas · ${v.leyenda}`
            : `${absoluta >= 0 ? '+' : ''}${absoluta} llamadas (${v.valor.toFixed(1)} %) frente a ${data.periodo}`,
        );
      },
      // Que falle la comparación no invalida el reporte principal.
      error: () => this.reporteComparado.set(null),
    });
  }
}
