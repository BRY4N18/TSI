import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../shared/ui/list-states/list-table.styles';
import { FacturacionApiService } from '../../services/facturacion-api.service';
import type { ExcepcionFacturacion, TipoExcepcion } from '../../services/models/monitoreo.types';

/** Qué hacer con cada tipo. Se deriva del tipo, no viene del backend. */
const ACCION_SUGERIDA: Record<TipoExcepcion, string> = {
  reintentos_agotados: 'Emitir la factura manualmente.',
  no_tarificable:
    'Configurar el precio de excedente del plan (CU-O26) y volver a ejecutar el corte.',
};

const ETIQUETA_TIPO: Record<TipoExcepcion, string> = {
  reintentos_agotados: 'Reintentos agotados',
  no_tarificable: 'No tarificable',
};

/**
 * Cola de excepciones de facturación (RF-APM-013).
 *
 * La única superficie de este módulo donde **no mirar cuesta dinero**.
 * RN-APM-014 dice que una factura de excedente nunca debe quedar
 * silenciosamente sin crearse; hasta que existió esta pantalla, el único aviso
 * era un correo que podía perderse.
 *
 * Dos tipos que **no son el mismo problema**:
 *
 * - `reintentos_agotados`: la factura existe y su emisión falló tres veces.
 * - `no_tarificable`: **no hay factura** — el plan no tiene tarifa con la que
 *   calcularla. Su columna de importe va vacía, no en cero: un 0,00 diría «se
 *   facturó nada», y la verdad es que no se pudo calcular.
 *
 * **No hay botón de emitir**: no existe endpoint de emisión manual, y un botón
 * que no hace nada es peor que decir cuál es el siguiente paso (FR-UI-135).
 */
@Component({
  selector: 'app-excepciones-facturacion',
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
      <header class="flex flex-wrap items-center justify-between gap-3">
        <h1 class="m-0 text-2xl font-bold text-text-primary">Excepciones de facturación</h1>
        <div class="flex items-end gap-3">
          <label class="flex flex-col gap-1 text-sm">
            <span class="text-xs uppercase tracking-wide text-text-secondary">Año</span>
            <input
              type="number"
              class="tsi-input"
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
              class="tsi-input"
              [ngModel]="mes()"
              (ngModelChange)="mes.set(+$event)"
              data-testid="input-mes"
            />
          </label>
          <button
            type="button"
            class="tsi-btn tsi-btn-ghost"
            (click)="cargar()"
            data-testid="btn-consultar"
          >
            Consultar
          </button>
        </div>
      </header>

      @if (cargando()) {
        <app-list-loading-skeleton [count]="4" />
      } @else if (error()) {
        <app-list-error-state [message]="error()!" (retry)="cargar()" />
      } @else if (excepciones().length === 0) {
        <!-- Aquí el vacío es la BUENA noticia: se redacta en positivo. -->
        <app-list-empty-state
          message="No hay excepciones de facturación pendientes. Todo el excedente del período se facturó correctamente."
          icon="circle-check"
        />
      } @else {
        <p class="mt-4 text-sm text-text-secondary" data-testid="resumen">
          {{ contadorAgotados() }} con reintentos agotados ·
          {{ contadorNoTarificables() }} sin tarifa configurada
        </p>

        <div class="mt-3 overflow-hidden rounded-md border border-border-default">
          <table class="hidden w-full border-collapse text-sm md:table">
            <thead>
              <tr class="bg-bg-surface text-left text-xs uppercase text-text-primary">
                <th class="px-4 py-3">Tipo</th>
                <th class="px-4 py-3">Partner</th>
                <th class="px-4 py-3">Período</th>
                <th class="px-4 py-3 text-right">Importe</th>
                <th class="px-4 py-3 text-right">Intentos</th>
                <th class="px-4 py-3">Último resultado</th>
                <th class="px-4 py-3">Acción sugerida</th>
              </tr>
            </thead>
            <tbody>
              @for (e of excepciones(); track e.idpartner + e.tipo + e.periodo) {
                <tr class="border-t border-border-default" [attr.data-testid]="'fila-' + e.tipo">
                  <td class="px-4 py-3">
                    <span
                      class="rounded-md bg-alert-warning-bg px-2 py-1 text-xs font-medium text-alert-warning"
                      [attr.data-testid]="'badge-' + e.tipo"
                    >
                      {{ etiqueta(e.tipo) }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-text-primary">{{ e.nombrepartner }}</td>
                  <td class="px-4 py-3 font-mono text-text-secondary">{{ e.periodo }}</td>
                  <!-- Vacío, NO 0,00: sin tarifa no se pudo calcular nada -->
                  <td
                    class="px-4 py-3 text-right font-mono text-text-primary"
                    [attr.data-testid]="'importe-' + e.tipo"
                  >
                    {{ importe(e) }}
                  </td>
                  <td class="px-4 py-3 text-right font-mono text-text-secondary">
                    {{ e.intentos === null ? '' : e.intentos }}
                  </td>
                  <td class="px-4 py-3 text-text-secondary">{{ e.ultimo_resultado }}</td>
                  <td class="px-4 py-3 text-text-secondary" [attr.data-testid]="'accion-' + e.tipo">
                    {{ accion(e.tipo) }}
                  </td>
                </tr>
              }
            </tbody>
          </table>

          <ul class="m-0 list-none space-y-3 p-3 md:hidden">
            @for (e of excepciones(); track e.idpartner + e.tipo + e.periodo) {
              <li class="rounded-md border border-border-default bg-bg-surface p-4 text-sm">
                <div class="flex items-center justify-between gap-2">
                  <span class="font-medium text-text-primary">{{ e.nombrepartner }}</span>
                  <span
                    class="rounded-md bg-alert-warning-bg px-2 py-1 text-xs font-medium text-alert-warning"
                  >
                    {{ etiqueta(e.tipo) }}
                  </span>
                </div>
                <p class="mt-2 text-text-secondary">
                  {{ e.periodo }} · {{ importe(e) || 'sin importe' }}
                </p>
                <p class="mt-1 text-text-secondary">{{ accion(e.tipo) }}</p>
              </li>
            }
          </ul>
        </div>
      }
    </section>
  `,
})
export class ExcepcionesFacturacionPage implements OnInit {
  private readonly api = inject(FacturacionApiService);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;
  readonly anio = signal(new Date().getFullYear());
  readonly mes = signal(new Date().getMonth() + 1);

  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);
  readonly excepciones = signal<ExcepcionFacturacion[]>([]);
  readonly contadorAgotados = signal(0);
  readonly contadorNoTarificables = signal(0);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.error.set(null);
    this.api.excepciones(this.anio(), this.mes()).subscribe({
      next: ({ data, meta }) => {
        this.excepciones.set(data ?? []);
        this.contadorAgotados.set(meta?.reintentos_agotados ?? 0);
        this.contadorNoTarificables.set(meta?.no_tarificables ?? 0);
        this.cargando.set(false);
      },
      error: (err: { status?: number }) => {
        this.error.set(
          err?.status === 403
            ? 'No tienes acceso a esta información.'
            : 'No se pudieron cargar las excepciones.',
        );
        this.cargando.set(false);
      },
    });
  }

  etiqueta(tipo: TipoExcepcion): string {
    return ETIQUETA_TIPO[tipo];
  }

  accion(tipo: TipoExcepcion): string {
    return ACCION_SUGERIDA[tipo];
  }

  /** Cadena vacía cuando no hay importe: nunca «0,00». */
  importe(e: ExcepcionFacturacion): string {
    return e.importe === null
      ? ''
      : e.importe.toLocaleString('es-EC', { style: 'currency', currency: 'USD' });
  }
}
