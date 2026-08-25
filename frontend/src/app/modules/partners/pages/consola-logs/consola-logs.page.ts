import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../shared/ui/list-states/list-table.styles';
import { MonitoreoApiService } from '../../services/monitoreo-api.service';
import { PartnerApiService } from '../../services/partner-api.service';
import {
  ETIQUETA_CODIGO,
  TONO_CODIGO,
  claseCodigo,
  formatearInstante,
  formatearIp,
} from '../../services/models/monitoreo.types';
import type { LogLlamada } from '../../services/models/monitoreo.types';
import type { PartnerListItem } from '../../services/models/partner.types';

/** Tamaño de página. El endpoint admite hasta 500. */
const LIMITE = 50;
/** Cadencia del auto-refresco, cuando el usuario lo enciende. */
const REFRESCO_MS = 30_000;

/**
 * Consola de registros de API (RF-APM-008).
 *
 * **Todo se consulta a la base, nada se filtra en memoria.**
 *
 * Es el mismo patrón que el resto del sistema (`lista-partners`, expedientes,
 * unidades): cada cambio de filtro dispara una consulta nueva y la paginación
 * es por cursor. La alternativa —traer una ventana y filtrarla en el navegador—
 * tenía dos defectos que no son de rendimiento sino de veracidad:
 *
 * 1. **Falsa exhaustividad.** Filtrar por «500» sobre los últimos 50 registros
 *    haría creer al usuario que no hay más errores de plataforma en toda la
 *    historia del partner, cuando solo no los hay en esa ventana.
 * 2. **Descuadre con la paginación.** El recuento de la página dejaría de
 *    coincidir con lo que el servidor devolvió, y «Cargar más» traería filas
 *    que el filtro local volvería a esconder.
 *
 * Sigue exigiendo elegir partner: el endpoint devuelve 400 sin `idpartner` y no
 * existe vista global. La UI se adelanta en vez de provocar el error.
 */
@Component({
  selector: 'app-consola-logs',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    TablerIconComponent,
    ListEmptyStateComponent,
    ListErrorStateComponent,
    ListLoadingSkeletonComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <header class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex flex-wrap items-center gap-3">
          <h1 class="m-0 text-2xl font-bold text-text-primary">Registros de API</h1>
          <span class="inline-flex items-center gap-2 text-xs text-text-secondary" data-testid="sincronizacion">
            <span class="h-2 w-2 rounded-full bg-alert-success"></span>
            @if (datosHasta()) {
              Datos hasta {{ instante(datosHasta()!) }}
            } @else {
              Sin datos cargados
            }
          </span>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <button
            type="button"
            class="tsi-btn tsi-btn-ghost"
            (click)="consultar()"
            data-testid="btn-actualizar"
          >
            <app-tabler-icon name="refresh" [size]="16" />
            Actualizar
          </button>
          <label class="flex items-center gap-2 text-sm text-text-secondary">
            <input
              type="checkbox"
              [ngModel]="autoRefresco()"
              (ngModelChange)="alternarAutoRefresco($event)"
              data-testid="chk-auto-refresco"
            />
            Auto-refresco (30 s)
          </label>
        </div>
      </header>

      <p class="mt-2 text-xs text-text-secondary" data-testid="leyenda-ingesta">
        «Tiempo real» está limitado por la ingesta: el consumo de los últimos segundos puede no
        aparecer todavía.
      </p>

      <!-- Filtros. Cada cambio consulta a la base: no se filtra en memoria. -->
      <div class="mt-4 flex flex-wrap items-end gap-4 rounded-md border border-border-default bg-bg-surface p-4">
        <label class="flex flex-col gap-1 text-sm">
          <span class="text-xs uppercase tracking-wide text-text-secondary">Partner</span>
          <select
            class="tsi-select"
            [ngModel]="idpartner()"
            (ngModelChange)="cambiarPartner($event)"
            data-testid="select-partner"
          >
            <option [ngValue]="null">Elige un partner…</option>
            @for (p of partners(); track p.idpartner) {
              <option [ngValue]="p.idpartner">{{ p.nombrepartner }}</option>
            }
          </select>
        </label>

        <label class="flex items-center gap-2 text-sm text-text-secondary">
          <input
            type="checkbox"
            [ngModel]="soloErrores()"
            (ngModelChange)="cambiarSoloErrores($event)"
            data-testid="chk-solo-errores"
          />
          Solo errores
        </label>

        <label class="flex flex-col gap-1 text-sm">
          <span class="text-xs uppercase tracking-wide text-text-secondary">Código HTTP</span>
          <input
            type="number"
            class="tsi-input"
            placeholder="Ej. 429"
            [ngModel]="filtroCodigo()"
            (ngModelChange)="cambiarCodigo($event)"
            data-testid="input-codigo"
          />
        </label>

        <label class="flex flex-col gap-1 text-sm">
          <span class="text-xs uppercase tracking-wide text-text-secondary">Desde</span>
          <input
            type="date"
            class="tsi-input"
            [ngModel]="filtroDesde()"
            (ngModelChange)="cambiarDesde($event)"
            data-testid="input-desde"
          />
        </label>

        <label class="flex flex-col gap-1 text-sm">
          <span class="text-xs uppercase tracking-wide text-text-secondary">Hasta</span>
          <input
            type="date"
            class="tsi-input"
            [ngModel]="filtroHasta()"
            (ngModelChange)="cambiarHasta($event)"
            data-testid="input-hasta"
          />
        </label>

        <p class="basis-full text-xs text-text-secondary" data-testid="alcance-filtros">
          Los filtros se aplican sobre <strong>todo el historial</strong> del partner, no solo
          sobre lo que se ve en pantalla.
        </p>
      </div>

      @if (idpartner() === null) {
        <app-list-empty-state
          message="Elige un partner para ver sus registros de API."
          icon="filter"
        />
      } @else if (cargando()) {
        <app-list-loading-skeleton [count]="6" />
      } @else if (error()) {
        <app-list-error-state [message]="error()!" (retry)="consultar()" />
      } @else if (logs().length === 0) {
        <app-list-empty-state
          message="Sin llamadas registradas para este partner con los filtros aplicados."
          icon="list"
        />
      } @else {
        <div class="mt-4 overflow-hidden rounded-md border border-border-default">
          <table class="hidden w-full border-collapse text-sm md:table">
            <thead>
              <tr class="bg-bg-surface text-left text-xs uppercase text-text-primary">
                <th class="px-4 py-3">Id</th>
                <th class="px-4 py-3">Fecha</th>
                <th class="px-4 py-3">Endpoint</th>
                <th class="px-4 py-3">Código</th>
                <th class="px-4 py-3 text-right">Latencia</th>
                <th class="px-4 py-3">IP</th>
                <th class="px-4 py-3 text-right">Acción</th>
              </tr>
            </thead>
            <tbody>
              @for (log of logs(); track log.idlogllamadaapi) {
                <tr class="border-t border-border-default" data-testid="fila-log">
                  <td class="px-4 py-3 font-mono text-text-secondary">{{ log.idlogllamadaapi }}</td>
                  <td class="px-4 py-3 text-text-secondary">{{ instante(log.fechallamada) }}</td>
                  <td class="px-4 py-3 font-mono text-text-primary">
                    {{ log.metodohttp }} {{ log.endpoint }}
                  </td>
                  <td class="px-4 py-3">
                    <span
                      class="rounded-md px-2 py-1 text-xs font-medium"
                      [class]="tono(log.codigohttp)"
                      [attr.data-testid]="'badge-' + log.codigohttp"
                    >
                      {{ log.codigohttp }} · {{ etiqueta(log.codigohttp) }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-right font-mono text-text-primary">
                    {{ log.latenciams }} ms
                  </td>
                  <td class="px-4 py-3 font-mono text-text-secondary">{{ ip(log.iporigen) }}</td>
                  <td class="px-4 py-3 text-right">
                    <!-- Solo el ojo: la tabla es append-only, nada que editar -->
                    <a
                      [routerLink]="['/partners/consola/logs', log.idlogllamadaapi]"
                      [queryParams]="{ idpartner: log.idpartner }"
                      class="inline-flex h-11 w-11 items-center justify-center text-text-secondary"
                      aria-label="Ver detalles"
                      title="Ver detalles"
                      data-testid="btn-ver"
                    >
                      <app-tabler-icon name="eye" [size]="18" />
                    </a>
                  </td>
                </tr>
              }
            </tbody>
          </table>

          <ul class="m-0 list-none space-y-3 p-3 md:hidden">
            @for (log of logs(); track log.idlogllamadaapi) {
              <li class="rounded-md border border-border-default bg-bg-surface p-4 text-sm">
                <div class="flex items-center justify-between gap-2">
                  <span class="font-mono text-text-primary">{{ log.metodohttp }} {{ log.endpoint }}</span>
                  <span class="rounded-md px-2 py-1 text-xs font-medium" [class]="tono(log.codigohttp)">
                    {{ log.codigohttp }}
                  </span>
                </div>
                <p class="mt-2 text-text-secondary">
                  {{ instante(log.fechallamada) }} · {{ log.latenciams }} ms · {{ ip(log.iporigen) }}
                </p>
              </li>
            }
          </ul>
        </div>

        @if (siguienteCursor() !== null) {
          <div class="mt-4 flex justify-center">
            <button
              type="button"
              class="tsi-btn tsi-btn-ghost"
              [disabled]="cargandoMas()"
              (click)="cargarMas()"
              data-testid="btn-cargar-mas"
            >
              {{ cargandoMas() ? 'Cargando…' : 'Cargar más' }}
            </button>
          </div>
        }

        <p class="mt-3 text-xs text-text-secondary" data-testid="pie-tabla">
          {{ logs().length }} registros mostrados.
        </p>
      }
    </section>
  `,
})
export class ConsolaLogsPage implements OnInit, OnDestroy {
  private readonly monitoreo = inject(MonitoreoApiService);
  private readonly partnersApi = inject(PartnerApiService);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;

  readonly partners = signal<PartnerListItem[]>([]);
  readonly idpartner = signal<number | null>(null);
  readonly soloErrores = signal(false);
  readonly filtroCodigo = signal<number | null>(null);
  readonly filtroDesde = signal('');
  readonly filtroHasta = signal('');
  /** Apagado al entrar: refrescar más rápido que la ingesta no trae dato nuevo. */
  readonly autoRefresco = signal(false);

  readonly cargando = signal(false);
  readonly cargandoMas = signal(false);
  readonly error = signal<string | null>(null);
  readonly logs = signal<LogLlamada[]>([]);
  readonly siguienteCursor = signal<number | null>(null);
  /** La otra mitad del cursor: sin ella la página siguiente repite filas. */
  readonly siguienteCursorFecha = signal<number | null>(null);
  readonly datosHasta = signal<number | null>(null);

  private temporizador: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    this.partnersApi.listar({ limit: 100 }).subscribe({
      next: ({ data }) => this.partners.set(data ?? []),
      error: () => this.partners.set([]),
    });
  }

  ngOnDestroy(): void {
    this.detenerAutoRefresco();
  }

  // --- Cada cambio de filtro es una consulta nueva -------------------------

  cambiarPartner(id: number | null): void {
    this.idpartner.set(id);
    this.consultar();
  }

  cambiarSoloErrores(valor: boolean): void {
    this.soloErrores.set(valor);
    this.consultar();
  }

  cambiarCodigo(valor: number | string | null): void {
    const codigo = valor === '' || valor === null ? null : Number(valor);
    this.filtroCodigo.set(Number.isFinite(codigo as number) ? (codigo as number) : null);
    this.consultar();
  }

  cambiarDesde(valor: string): void {
    this.filtroDesde.set(valor);
    this.consultar();
  }

  cambiarHasta(valor: string): void {
    this.filtroHasta.set(valor);
    this.consultar();
  }

  /** Primera página: reemplaza lo que hubiera y reinicia el cursor. */
  consultar(): void {
    const id = this.idpartner();
    if (id === null) {
      this.logs.set([]);
      this.siguienteCursor.set(null);
      this.siguienteCursorFecha.set(null);
      return;
    }
    this.cargando.set(true);
    this.error.set(null);
    this.monitoreo.logs(this.filtros(id)).subscribe({
      next: (res) => {
        const filas = res.data ?? [];
        this.logs.set(filas);
        this.siguienteCursor.set(res.meta?.pagination?.next_cursor ?? null);
        this.siguienteCursorFecha.set(res.meta?.pagination?.next_cursor_fecha ?? null);
        this.datosHasta.set(filas.length ? filas[0].fechallamada : Date.now());
        this.cargando.set(false);
      },
      error: (err: { status?: number }) => {
        this.error.set(this.mensajeDe(err));
        this.cargando.set(false);
      },
    });
  }

  /** Página siguiente: **otra consulta**, con el cursor que dio el servidor. */
  cargarMas(): void {
    const id = this.idpartner();
    const cursor = this.siguienteCursor();
    if (id === null || cursor === null) {
      return;
    }
    this.cargandoMas.set(true);
    this.monitoreo
      .logs({ ...this.filtros(id), cursor, cursorFecha: this.siguienteCursorFecha() })
      .subscribe({
      next: (res) => {
        this.logs.update((previos) => [...previos, ...(res.data ?? [])]);
        this.siguienteCursor.set(res.meta?.pagination?.next_cursor ?? null);
        this.siguienteCursorFecha.set(res.meta?.pagination?.next_cursor_fecha ?? null);
        this.cargandoMas.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar la siguiente página.');
        this.cargandoMas.set(false);
      },
    });
  }

  alternarAutoRefresco(activo: boolean): void {
    this.autoRefresco.set(activo);
    this.detenerAutoRefresco();
    if (activo) {
      this.temporizador = setInterval(() => this.consultar(), REFRESCO_MS);
    }
  }

  // --- Auxiliares ----------------------------------------------------------

  private filtros(idpartner: number) {
    return {
      idpartner,
      soloErrores: this.soloErrores(),
      codigohttp: this.filtroCodigo(),
      desdeMs: this.aEpoch(this.filtroDesde()),
      // `hasta` es exclusivo en el backend: se suma un día para que el rango
      // incluya la fecha que el usuario eligió, que es lo que espera.
      hastaMs: this.aEpoch(this.filtroHasta(), 86_400_000),
      limit: LIMITE,
    };
  }

  private aEpoch(fecha: string, sumar = 0): number | null {
    if (!fecha) {
      return null;
    }
    const ms = new Date(fecha).getTime();
    return Number.isFinite(ms) ? ms + sumar : null;
  }

  private mensajeDe(err: { status?: number }): string {
    if (err?.status === 403) {
      return 'No tienes acceso a esta información.';
    }
    if (err?.status === 400) {
      return 'Revisa los filtros: alguno tiene un valor no válido.';
    }
    return 'No se pudieron cargar los registros.';
  }

  private detenerAutoRefresco(): void {
    if (this.temporizador !== null) {
      clearInterval(this.temporizador);
      this.temporizador = null;
    }
  }

  tono(codigo: number): string {
    return TONO_CODIGO[claseCodigo(codigo)];
  }

  etiqueta(codigo: number): string {
    return ETIQUETA_CODIGO[claseCodigo(codigo)];
  }

  ip(entero: number): string {
    return formatearIp(entero);
  }

  instante(ms: number): string {
    return formatearInstante(ms);
  }
}
