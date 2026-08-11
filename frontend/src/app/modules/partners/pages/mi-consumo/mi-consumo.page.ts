import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../shared/ui/list-states/list-table.styles';
import { MonitoreoApiService } from '../../services/monitoreo-api.service';
import { PartnerApiService } from '../../services/partner-api.service';
import {
  COPY_CUPO,
  COPY_CUPO_SUSPENDIDO,
  ETIQUETA_CODIGO,
  TONO_CODIGO,
  TONO_CUPO,
  claseCodigo,
  cuentaComoConsumo,
  estadoCupo,
  formatearInstante,
  importeExcedente,
  porcentajeCupo,
  textoImporte,
  textoPorcentaje,
} from '../../services/models/monitoreo.types';
import type { ConsumoPartner, LogLlamada } from '../../services/models/monitoreo.types';
import type { PartnerDetalle } from '../../services/models/partner.types';

/**
 * Panel de consumo del partner (RF-APM-007, RF-APM-008).
 *
 * La pantalla más delicada de esta capa, y no por su lógica —que es mínima—
 * sino por lo que comunica. **Superar el cupo NO interrumpe el servicio**
 * (RN-APM-002): el exceso es un coste previsto, no un fallo. Por eso el bloque
 * de cupo usa tono informativo en sus cuatro estados, incluido el de 150 %.
 *
 * Si alguien lo ve y piensa «esto debería estar en rojo», la respuesta está en
 * el SRS, que documentó la regla *«para que nadie la corrija asumiendo que
 * debería bloquear»*. El test `mi-consumo-sin-alarma.spec.ts` lo protege.
 *
 * El primer requisito de todo es saber **cuál es su partner**: el token solo
 * lleva `idusuario`, así que sin `GET /partners/me` no hay nada que pedir.
 */
@Component({
  selector: 'app-mi-consumo',
  standalone: true,
  imports: [
    TablerIconComponent,
    ListEmptyStateComponent,
    ListErrorStateComponent,
    ListLoadingSkeletonComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <header class="flex flex-wrap items-center gap-3">
        <h1 class="m-0 text-2xl font-bold text-text-primary">Mi consumo</h1>
        <!-- El entorno se dice con TEXTO, no solo con color (RN-APM-001). -->
        <span
          class="inline-flex items-center gap-1.5 rounded-md bg-alert-info-bg px-2 py-1 text-xs font-medium text-alert-info"
          data-testid="badge-entorno"
        >
          Producción
        </span>
      </header>

      @if (cargando()) {
        <app-list-loading-skeleton [count]="3" />
      } @else if (errorCarga()) {
        <app-list-error-state
          [message]="errorCarga()!"
          [retryLabel]="puedeReintentar() ? 'Reintentar' : ''"
          (retry)="cargar()"
        />
      } @else {
        @if (consumo(); as c) {
          @if (suspendido()) {
            <!-- Lectura permitida estando suspendido (RN-APM-017): es lo que le
                 permite entender su situación. -->
            <div
              class="mt-4 rounded-lg border border-border-default bg-alert-info-bg p-4 text-sm text-alert-info"
              data-testid="banner-suspendido"
            >
              Tu acceso de integración está suspendido. Puedes seguir consultando tu consumo y tu
              historial.
            </div>
          }

          <!-- Bloque 1 — Cupo. Tono informativo en TODOS los estados. -->
          <div
            class="mt-4 rounded-lg border border-border-default bg-bg-surface p-6"
            data-testid="bloque-cupo"
          >
            <h2 class="m-0 mb-4 text-lg font-semibold text-text-primary">Cupo del período</h2>
            <div class="flex flex-wrap items-baseline gap-3">
              <span
                class="rounded-md px-2 py-1 font-mono text-2xl font-bold"
                [class]="tonoCupo"
                data-testid="porcentaje-cupo"
              >
                {{ porcentaje(c) }}
              </span>
              <span class="text-sm text-text-secondary" data-testid="llamadas-de-cupo">
                {{ c.llamadas.toLocaleString('es-EC') }} llamadas
              </span>
            </div>
            @if (copyCupo(c)) {
              <p class="mt-3 text-sm text-text-secondary" data-testid="copy-cupo">
                {{ copyCupo(c) }}
              </p>
            }
          </div>

          <!-- Bloque 2 — Actividad -->
          <div class="mt-4 grid gap-4 sm:grid-cols-3">
            <div class="rounded-lg border border-border-default bg-bg-surface p-6">
              <p class="m-0 text-xs uppercase tracking-wide text-text-secondary">Llamadas</p>
              <p class="m-0 mt-1 font-mono text-xl text-text-primary" data-testid="kpi-llamadas">
                {{ c.llamadas.toLocaleString('es-EC') }}
              </p>
            </div>
            <div class="rounded-lg border border-border-default bg-bg-surface p-6">
              <p class="m-0 text-xs uppercase tracking-wide text-text-secondary">Errores</p>
              <p class="m-0 mt-1 font-mono text-xl text-text-primary" data-testid="kpi-errores">
                {{ c.errores.toLocaleString('es-EC') }}
              </p>
            </div>
            <div class="rounded-lg border border-border-default bg-bg-surface p-6">
              <p class="m-0 text-xs uppercase tracking-wide text-text-secondary">Latencia media</p>
              <p class="m-0 mt-1 font-mono text-xl text-text-primary" data-testid="kpi-latencia">
                {{ c.latencia_media_ms }} ms
              </p>
            </div>
          </div>

          <!-- Bloque 4 — Excedente: solo si hay algo que decir -->
          @if (mostrarExcedente(c)) {
            <div
              class="mt-4 rounded-lg border border-border-default bg-bg-surface p-6"
              data-testid="bloque-excedente"
            >
              <h2 class="m-0 mb-2 text-lg font-semibold text-text-primary">Excedente estimado</h2>
              <p class="m-0 font-mono text-xl text-text-primary" data-testid="importe-excedente">
                {{ importe(c) }}
              </p>
              <p class="mt-2 text-sm text-text-secondary">
                {{ c.llamadas_excedentes.toLocaleString('es-EC') }} llamadas por encima del cupo.
                Se facturará al cierre del período.
              </p>
            </div>
          }

          <!-- Bloque 3 — Errores del partner: autodiagnóstico (RN-APM-009) -->
          <div
            class="mt-4 rounded-lg border border-border-default bg-bg-surface p-6"
            data-testid="bloque-errores"
          >
            <h2 class="m-0 mb-4 text-lg font-semibold text-text-primary">
              Errores de tu integración
            </h2>
            @if (erroresNoDisponibles()) {
              <!-- NO se dice «sin errores» cuando no se pudieron consultar: eso
                   afirmaría que la integración está sana sin haberlo
                   comprobado. Se detectó verificando contra la app real. -->
              <app-list-error-state
                message="No se pudieron cargar tus errores recientes. Tu consumo sí está actualizado."
                retryLabel=""
              />
            } @else if (errores().length === 0) {
              <app-list-empty-state
                message="Sin errores en el período. Tu integración está respondiendo correctamente."
                icon="circle-check"
              />
            } @else {
              <ul class="m-0 list-none space-y-2 p-0">
                @for (log of errores(); track log.idlogllamadaapi) {
                  <li
                    class="flex flex-wrap items-center gap-3 border-b border-border-default pb-2 text-sm last:border-0"
                    data-testid="fila-error"
                  >
                    <span
                      class="rounded-md px-2 py-1 text-xs font-medium"
                      [class]="tonoCodigo(log.codigohttp)"
                      [attr.data-testid]="'badge-' + log.codigohttp"
                    >
                      {{ log.codigohttp }} · {{ etiquetaCodigo(log.codigohttp) }}
                    </span>
                    <span class="font-mono text-text-primary">{{ log.metodohttp }} {{ log.endpoint }}</span>
                    <span class="text-text-secondary">{{ instante(log.fechallamada) }}</span>
                    @if (!facturable(log.codigohttp)) {
                      <span class="text-xs text-text-secondary" data-testid="nota-no-facturable">
                        No cuenta como consumo facturable
                      </span>
                    }
                  </li>
                }
              </ul>
            }
          </div>

          <!-- «Tiempo real» tiene un límite: se dice, no se promete. -->
          <p class="mt-4 text-xs text-text-secondary" data-testid="datos-hasta">
            Datos disponibles hasta {{ instante(c.datos_hasta) }}. La ingesta tarda unos segundos,
            así que el consumo más reciente puede no aparecer todavía.
          </p>
        }
      }
    </section>
  `,
})
export class MiConsumoPage implements OnInit {
  private readonly partners = inject(PartnerApiService);
  private readonly monitoreo = inject(MonitoreoApiService);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;
  readonly tonoCupo = TONO_CUPO;

  readonly cargando = signal(true);
  readonly errorCarga = signal<string | null>(null);
  readonly puedeReintentar = signal(true);
  readonly partner = signal<PartnerDetalle | null>(null);
  readonly consumo = signal<ConsumoPartner | null>(null);
  readonly errores = signal<LogLlamada[]>([]);
  /** Distingue «no hay errores» de «no se pudieron consultar». */
  readonly erroresNoDisponibles = signal(false);

  readonly suspendido = computed(() => this.partner()?.activo === false);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.errorCarga.set(null);
    this.puedeReintentar.set(true);

    // Paso obligatorio y primero: sin el idpartner no hay métricas que pedir.
    this.partners.miPartner().subscribe({
      next: ({ data }) => {
        this.partner.set(data);
        this.cargarConsumo(data.idpartner);
      },
      error: (err: { status?: number }) => {
        if (err?.status === 404) {
          // Reintentar no lo vinculará a ningún partner: no se ofrece.
          this.puedeReintentar.set(false);
          this.errorCarga.set(
            'Tu usuario no está vinculado a ningún partner. Contacta al administrador.',
          );
        } else if (err?.status === 403) {
          this.puedeReintentar.set(false);
          this.errorCarga.set('No tienes acceso a esta información.');
        } else {
          this.errorCarga.set('No se pudieron cargar tus datos.');
        }
        this.cargando.set(false);
      },
    });
  }

  private cargarConsumo(idpartner: number): void {
    this.monitoreo.metricas(idpartner).subscribe({
      next: ({ data }) => {
        this.consumo.set(data);
        this.cargando.set(false);
      },
      error: () => {
        this.errorCarga.set('No se pudo cargar tu consumo.');
        this.cargando.set(false);
      },
    });

    this.erroresNoDisponibles.set(false);
    this.monitoreo.logs({ idpartner, soloErrores: true, limit: 20 }).subscribe({
      // Fail-open para el consumo, pero SIN mentir sobre los errores: si la
      // consulta falla se dice, en vez de mostrar «sin errores» —que afirmaría
      // que la integración está sana sin haberlo comprobado.
      next: ({ data }) => this.errores.set(data ?? []),
      error: () => {
        this.errores.set([]);
        this.erroresNoDisponibles.set(true);
      },
    });
  }

  // --- Presentación (toda la traducción de centinelas vive en el helper) ----

  porcentaje(c: ConsumoPartner): string {
    return textoPorcentaje(porcentajeCupo(c));
  }

  importe(c: ConsumoPartner): string {
    return textoImporte(importeExcedente(c));
  }

  copyCupo(c: ConsumoPartner): string {
    // Un partner suspendido NO puede leer «tu servicio no se interrumpe»: su
    // acceso sí está cortado, aunque no sea por el cupo.
    const copys = this.suspendido() ? COPY_CUPO_SUSPENDIDO : COPY_CUPO;
    return copys[estadoCupo(c)];
  }

  /** Se muestra si hay exceso, o si lo hay pero no se puede tarificar. */
  mostrarExcedente(c: ConsumoPartner): boolean {
    return c.llamadas_excedentes > 0 || c.excedente_estimado === null;
  }

  tonoCodigo(codigo: number): string {
    return TONO_CODIGO[claseCodigo(codigo)];
  }

  etiquetaCodigo(codigo: number): string {
    return ETIQUETA_CODIGO[claseCodigo(codigo)];
  }

  facturable(codigo: number): boolean {
    return cuentaComoConsumo(codigo);
  }

  instante(ms: number): string {
    return formatearInstante(ms);
  }
}
