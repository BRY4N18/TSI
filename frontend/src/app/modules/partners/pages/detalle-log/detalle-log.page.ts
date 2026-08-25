import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../shared/ui/list-states/list-table.styles';
import { MonitoreoApiService } from '../../services/monitoreo-api.service';
import {
  ETIQUETA_CODIGO,
  TONO_CODIGO,
  claseCodigo,
  cuentaComoConsumo,
  formatearInstante,
  formatearIp,
} from '../../services/models/monitoreo.types';
import type { LogLlamada } from '../../services/models/monitoreo.types';

/**
 * Detalle de un registro de llamada — workpanel en **modo Ver únicamente**.
 *
 * No hay modo Editar y no es una omisión: `Fact_LogLlamadaAPI` es append-only
 * (RN-APM-015). No existe nada que hacerle a un log, así que tampoco hay
 * acciones de dominio ni botón de guardado.
 *
 * Los datos van en un `<dl>`, no en `<input disabled>`: fingir un formulario de
 * solo lectura es justo lo que el design-system prohíbe.
 *
 * El endpoint no expone «un log por id», así que se recupera de la ventana del
 * partner. Es una limitación real del contrato, no una decisión de diseño.
 */
@Component({
  selector: 'app-detalle-log',
  standalone: true,
  imports: [
    RouterLink,
    TablerIconComponent,
    ListEmptyStateComponent,
    ListErrorStateComponent,
    ListLoadingSkeletonComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <a
        routerLink="/partners/consola/logs"
        class="inline-flex items-center gap-2 text-sm text-accent-primary"
        data-testid="volver"
      >
        <app-tabler-icon name="arrow-left" [size]="16" />
        Volver a los registros
      </a>

      <p class="mt-4 text-xs uppercase tracking-wide text-text-secondary" data-testid="eyebrow">
        Detalles
      </p>

      @if (cargando()) {
        <app-list-loading-skeleton [count]="3" />
      } @else if (error()) {
        <app-list-error-state [message]="error()!" (retry)="cargar()" />
      } @else {
        <!-- El alias "as" solo se admite en el @if primario, nunca en un
             @else if. Es un error que el compilador de TypeScript no detecta:
             solo lo caza ng test, y ya se coló varias veces en #07.
             (Y ojo: nada de comillas invertidas en estos comentarios; cierran
             el template literal y rompen el archivo entero.) -->
        @if (log(); as l) {
        <header class="mt-1 flex flex-wrap items-center gap-3">
          <h1 class="m-0 font-mono text-2xl font-bold text-text-primary">
            {{ l.metodohttp }} {{ l.endpoint }}
          </h1>
          <span
            class="rounded-md px-2 py-1 text-xs font-medium"
            [class]="tono(l.codigohttp)"
            data-testid="badge-codigo"
          >
            {{ l.codigohttp }} · {{ etiqueta(l.codigohttp) }}
          </span>
        </header>

        <div class="mt-4 rounded-md border border-border-default bg-bg-surface p-6">
          <dl class="grid grid-cols-[auto_1fr] gap-x-6 gap-y-3 text-sm">
            <dt class="text-xs uppercase tracking-wide text-text-secondary">Id</dt>
            <dd class="m-0 font-mono text-text-primary">{{ l.idlogllamadaapi }}</dd>
            <dt class="text-xs uppercase tracking-wide text-text-secondary">Fecha y hora</dt>
            <dd class="m-0 text-text-primary">{{ instante(l.fechallamada) }}</dd>
            <dt class="text-xs uppercase tracking-wide text-text-secondary">Latencia</dt>
            <dd class="m-0 font-mono text-text-primary">{{ l.latenciams }} ms</dd>
            <dt class="text-xs uppercase tracking-wide text-text-secondary">IP de origen</dt>
            <dd class="m-0 font-mono text-text-primary">{{ ip(l.iporigen) }}</dd>
            <dt class="text-xs uppercase tracking-wide text-text-secondary">Consumo</dt>
            <dd class="m-0 text-text-primary" data-testid="dd-consumo">
              {{ facturable(l.codigohttp) ? 'Cuenta como llamada facturable' : 'No cuenta como consumo facturable' }}
            </dd>
          </dl>
        </div>
        } @else {
          <app-list-empty-state
            message="No se encontró ese registro en la ventana cargada."
            icon="list"
          />
        }
      }
    </section>
  `,
})
export class DetalleLogPage implements OnInit {
  private readonly ruta = inject(ActivatedRoute);
  private readonly monitoreo = inject(MonitoreoApiService);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);
  readonly log = signal<LogLlamada | null>(null);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    const idlog = Number(this.ruta.snapshot.paramMap.get('idlog'));
    const idpartner = Number(this.ruta.snapshot.queryParamMap.get('idpartner'));
    this.cargando.set(true);
    this.error.set(null);

    if (!idpartner) {
      // Sin el partner el endpoint devuelve 400: se dice en vez de provocarlo.
      this.error.set('Abre el detalle desde la lista de registros.');
      this.cargando.set(false);
      return;
    }

    this.monitoreo.logs({ idpartner, limit: 500 }).subscribe({
      next: ({ data }) => {
        this.log.set((data ?? []).find((l) => l.idlogllamadaapi === idlog) ?? null);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar el registro.');
        this.cargando.set(false);
      },
    });
  }

  tono(codigo: number): string {
    return TONO_CODIGO[claseCodigo(codigo)];
  }

  etiqueta(codigo: number): string {
    return ETIQUETA_CODIGO[claseCodigo(codigo)];
  }

  facturable(codigo: number): boolean {
    return cuentaComoConsumo(codigo);
  }

  ip(entero: number): string {
    return formatearIp(entero);
  }

  instante(ms: number): string {
    return formatearInstante(ms);
  }
}
