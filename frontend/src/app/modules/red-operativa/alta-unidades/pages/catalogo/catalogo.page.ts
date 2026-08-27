import { ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import {
  Subject,
  TimeoutError,
  catchError,
  debounceTime,
  distinctUntilChanged,
  of,
  switchMap,
  takeUntil,
  timeout,
} from 'rxjs';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { NotificationService } from '../../../../../shared/notifications/notification.service';
import { ListEmptyStateComponent } from '../../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../../shared/ui/list-states/list-loading-skeleton.component';
import {
  LIST_ACTION_ICON_BTN_CLASS,
  LIST_FILTER_CONTROL_CLASS,
  LIST_FILTER_SELECT_CLASS,
  LIST_MOBILE_CARD_CLASS,
  LIST_ROW_CLASS,
  LIST_TABLE_CLASS,
  LIST_TABLE_TD_CLASS,
  LIST_TABLE_TD_PRIMARY_CLASS,
  LIST_TABLE_TH_CLASS,
  LIST_TABLE_TH_RIGHT_CLASS,
} from '../../../../../shared/ui/list-states/list-table.styles';
import { ListaSeleccionStorage } from '../../lista-seleccion.storage';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import {
  CatalogQueryState,
  ImportacionLoteData,
  TipoUnidadEmergencia,
  UnidadEmergenciaData,
} from '../../models/unidad-emergencia.contract';

/**
 * Columnas del CSV de importación en lote.
 *
 * ⚠️ La primera columna era `idcondado`: una clave interna del catálogo que un
 * proveedor de flota no tiene forma de conocer, y sin la cual el archivo entero
 * fallaba (hallazgo #16 de la revisión del 24/08/2026). Ahora se escribe el
 * **nombre** del condado y el backend lo resuelve; `estado` solo hace falta si
 * hay condados homónimos.
 *
 * El mismo orden se usa para exportar, para que exportar → editar → reimportar
 * sea un ciclo cerrado.
 */
const CSV_COLUMNAS = [
  'condado',
  'estado',
  'tipopropiedad',
  'placa',
  'contactoproveedor',
  'unidademergencia',
  'tipounidademergencia',
  'gmail',
] as const;

/** Comillas y separadores dentro de un campo romperían el archivo generado. */
function escaparCampoCsv(valor: string): string {
  return /[",\r\n]/.test(valor) ? `"${valor.replaceAll('"', '""')}"` : valor;
}

interface ColumnaCsv {
  nombre: string;
  obligatoria: string;
  admite: string;
}

/** Documentación que se muestra junto al selector de archivo. */
const CSV_DOCUMENTACION: ColumnaCsv[] = [
  { nombre: 'condado', obligatoria: 'Sí', admite: 'Nombre del condado (ej. Miami-Dade)' },
  { nombre: 'estado', obligatoria: 'Solo si el condado es ambiguo', admite: 'Nombre del estado' },
  { nombre: 'tipopropiedad', obligatoria: 'Sí', admite: 'Propia | Externa' },
  { nombre: 'placa', obligatoria: 'Sí', admite: '6 a 8 alfanuméricos, única' },
  {
    nombre: 'contactoproveedor',
    obligatoria: 'Solo si tipopropiedad es Externa',
    admite: 'Teléfono o contacto',
  },
  { nombre: 'unidademergencia', obligatoria: 'Sí', admite: 'Nombre de la unidad' },
  {
    nombre: 'tipounidademergencia',
    obligatoria: 'Sí',
    admite: 'Ambulancia | Grúa | Patrulla | Bomberos | Defensa Civil',
  },
  { nombre: 'gmail', obligatoria: 'Sí', admite: 'Correo del operador (recibe sus credenciales)' },
];

/** Fila de ejemplo de la plantilla: un archivo válido tal cual se descarga. */
const CSV_EJEMPLO = [
  'Miami-Dade',
  'Florida',
  'Externa',
  'ABC-1234',
  '5551234567',
  'Ambulancia Norte 1',
  'Ambulancia',
  'operador.norte1@ejemplo.com',
];

const LIST_TIMEOUT_MS = 10_000;
const PAGE_LIMIT = 20;

type BajaStep = 1 | 2 | 3;
type EstadoFiltro = 'todas' | 'activa' | 'baja';

interface BajaDialogState {
  step: BajaStep;
  idunidademergencia: number;
  placa: string;
  motivo: string;
}

interface ReactivarDialogState {
  step: 1 | 2;
  idunidademergencia: number;
  placa: string;
}

@Component({
  selector: 'app-red-operativa-catalogo-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TablerIconComponent,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  template: `
    <div class="mx-auto w-full max-w-5xl space-y-6 p-6">
      <header class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 class="tsi-display text-[28px] font-extrabold text-text-primary">Catálogo de unidades</h1>
<div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>
          <p class="mt-1 text-sm text-text-secondary">
            Flota del Proveedor — ver detalles, crear o editar en páginas dedicadas.
          </p>
        </div>
        <button
          type="button"
          data-testid="btn-nueva-unidad"
          (click)="irNueva()"
          class="tsi-btn tsi-btn-primary"
        >
          <app-tabler-icon name="plus" [size]="18" />
          Nueva unidad
        </button>
      </header>

      <section class="space-y-4 tsi-panel p-6">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="tsi-display text-lg font-semibold text-text-primary">Mis unidades</h2>
          <button
            type="button"
            data-testid="btn-actualizar-lista"
            (click)="cargarUnidades()"
            class="tsi-btn tsi-btn-primary"
          >
            Actualizar
          </button>
        </div>

        <div
          class="grid grid-cols-1 gap-3 sm:grid-cols-3"
          data-testid="catalogo-filtros"
        >
          <label class="block sm:col-span-1">
            <span class="mb-1 block text-xs font-medium text-text-secondary">Buscar</span>
            <input
              type="search"
              name="filtroQ"
              [(ngModel)]="filtroQ"
              (ngModelChange)="onFiltroTexto()"
              placeholder="Placa o nombre"
              data-testid="filtro-q"
              [class]="listFilterControlClass"
            />
          </label>
          <label class="block">
            <span class="mb-1 block text-xs font-medium text-text-secondary">Estado</span>
            <select
              name="filtroEstado"
              [(ngModel)]="filtroEstado"
              (change)="onFiltroSelect()"
              data-testid="filtro-estado"
              [class]="listFilterControlClassSelect"
            >
              <option value="todas">Todas</option>
              <option value="activa">Activa</option>
              <option value="baja">Baja</option>
            </select>
          </label>
          <label class="block">
            <span class="mb-1 block text-xs font-medium text-text-secondary">Tipo</span>
            <select
              name="filtroTipo"
              [(ngModel)]="filtroTipo"
              (change)="onFiltroSelect()"
              data-testid="filtro-tipo"
              [class]="listFilterControlClassSelect"
            >
              <option value="">Todos</option>
              @for (t of tiposUnidad; track t) {
                <option [value]="t">{{ t }}</option>
              }
            </select>
          </label>
        </div>

        @if (loading && unidades.length === 0 && !unidadesError) {
          <app-list-loading-skeleton [count]="3" />
        } @else if (unidadesError && unidades.length === 0) {
          <app-list-error-state [message]="unidadesError" (retry)="cargarUnidades()" />
        } @else if (!loading && unidades.length === 0) {
          <app-list-empty-state
            icon="car"
            [message]="
              tieneFiltros
                ? 'No hay unidades que coincidan con los filtros.'
                : 'Aún no hay unidades registradas.'
            "
          >
            @if (!tieneFiltros) {
              <button
                type="button"
                (click)="irNueva()"
                class="tsi-btn tsi-btn-primary"
              >
                Nueva unidad
              </button>
            }
          </app-list-empty-state>
        } @else {
          <table [class]="listTableClass" data-testid="tabla-unidades">
            <thead>
              <tr class="bg-bg-surface">
                <th [class]="listTableThClass">ID</th>
                <th [class]="listTableThClass">Placa</th>
                <th [class]="listTableThClass">Nombre</th>
                <th [class]="listTableThClass">Estado</th>
                <th [class]="listTableThRightClass">Acciones</th>
              </tr>
            </thead>
            <tbody>
              @for (u of unidades; track u.idunidademergencia) {
                <tr [class]="filaClass(u.idunidademergencia)">
                  <td [class]="listTableTdPrimaryClass + ' font-mono'">
                    {{ u.idunidademergencia }}
                  </td>
                  <td [class]="listTableTdClass + ' font-mono'">{{ u.placa }}</td>
                  <td [class]="listTableTdClass">{{ u.unidademergencia }}</td>
                  <td [class]="listTableTdClass">
                    <span
                      [class]="
                        u.activo
                          ? 'rounded-md bg-alert-success-bg px-2 py-1 text-xs text-alert-success'
                          : 'rounded-md bg-alert-critical-bg px-2 py-1 text-xs text-alert-critical'
                      "
                    >
                      {{ u.activo ? 'Activa' : 'Baja' }}
                    </span>
                  </td>
                  <td [class]="listTableTdClass + ' text-right'">
                    <div class="inline-flex items-center justify-end gap-1">
                      <button
                        type="button"
                        [class]="listActionIconBtnClass"
                        aria-label="Ver detalles"
                        title="Ver detalles"
                        data-testid="btn-ver-detalles"
                        (click)="irDetalle(u.idunidademergencia)"
                      >
                        <app-tabler-icon name="eye" [size]="18" />
                      </button>
                      <button
                        type="button"
                        [class]="listActionIconBtnClass"
                        aria-label="Editar unidad"
                        title="Editar unidad"
                        data-testid="btn-editar-unidad"
                        (click)="irEditar(u.idunidademergencia)"
                      >
                        <app-tabler-icon name="pencil" [size]="18" />
                      </button>
                      @if (u.activo) {
                        <button
                          type="button"
                          class="inline-flex h-11 w-11 items-center justify-center rounded-md text-alert-critical hover:bg-alert-critical-bg"
                          aria-label="Dar de baja"
                          title="Dar de baja"
                          data-testid="btn-baja-unidad"
                          (click)="iniciarBaja(u)"
                        >
                          <app-tabler-icon name="trash" [size]="18" />
                        </button>
                      } @else {
                        <button
                          type="button"
                          class="inline-flex h-11 w-11 items-center justify-center rounded-md text-accent-primary hover:bg-accent-primary/10"
                          aria-label="Reactivar unidad"
                          title="Reactivar unidad"
                          data-testid="btn-reactivar-unidad"
                          (click)="iniciarReactivar(u)"
                        >
                          <app-tabler-icon name="refresh" [size]="18" />
                        </button>
                      }
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>

          <!-- Mobile: cards apiladas -->
          <div class="grid gap-3 md:hidden" data-testid="tabla-unidades-mobile">
            @for (u of unidades; track u.idunidademergencia) {
              <div [class]="cardClass(u.idunidademergencia)">
                <div class="mb-2 flex items-center justify-between gap-2">
                  <span class="font-mono text-sm font-semibold text-text-primary">{{ u.placa }}</span>
                  <div class="inline-flex items-center gap-1">
                    <button
                      type="button"
                      [class]="listActionIconBtnClass"
                      aria-label="Ver detalles"
                      title="Ver detalles"
                      (click)="irDetalle(u.idunidademergencia)"
                    >
                      <app-tabler-icon name="eye" [size]="18" />
                    </button>
                    <button
                      type="button"
                      [class]="listActionIconBtnClass"
                      aria-label="Editar unidad"
                      title="Editar unidad"
                      (click)="irEditar(u.idunidademergencia)"
                    >
                      <app-tabler-icon name="pencil" [size]="18" />
                    </button>
                    @if (u.activo) {
                      <button
                        type="button"
                        class="inline-flex h-11 w-11 items-center justify-center rounded-md text-alert-critical hover:bg-alert-critical-bg"
                        aria-label="Dar de baja"
                        title="Dar de baja"
                        (click)="iniciarBaja(u)"
                      >
                        <app-tabler-icon name="trash" [size]="18" />
                      </button>
                    } @else {
                      <button
                        type="button"
                        class="inline-flex h-11 w-11 items-center justify-center rounded-md text-accent-primary hover:bg-accent-primary/10"
                        aria-label="Reactivar unidad"
                        title="Reactivar unidad"
                        (click)="iniciarReactivar(u)"
                      >
                        <app-tabler-icon name="refresh" [size]="18" />
                      </button>
                    }
                  </div>
                </div>
                <dl class="grid gap-1 text-sm">
                  <div class="flex justify-between gap-2">
                    <dt class="text-text-secondary">ID</dt>
                    <dd class="font-mono font-medium text-text-primary">{{ u.idunidademergencia }}</dd>
                  </div>
                  <div class="flex justify-between gap-2">
                    <dt class="text-text-secondary">Nombre</dt>
                    <dd class="truncate font-medium text-text-primary">{{ u.unidademergencia }}</dd>
                  </div>
                  <div class="flex justify-between gap-2">
                    <dt class="text-text-secondary">Estado</dt>
                    <dd
                      [class]="
                        u.activo
                          ? 'inline-flex rounded-md bg-alert-success-bg px-2 py-1 text-xs text-alert-success'
                          : 'inline-flex rounded-md bg-alert-critical-bg px-2 py-1 text-xs text-alert-critical'
                      "
                    >
                      {{ u.activo ? 'Activa' : 'Baja' }}
                    </dd>
                  </div>
                </dl>
              </div>
            }
          </div>

          <div class="flex flex-wrap items-center justify-between gap-3" data-testid="catalogo-pager">
            <p class="text-xs text-text-secondary">
              Hasta {{ pageLimit }} por página
              @if (unidades.length) {
                · {{ unidades.length }} en esta vista
              }
            </p>
            <div class="flex gap-2">
              <button
                type="button"
                data-testid="btn-pagina-anterior"
                [disabled]="!puedeAnterior || loading"
                (click)="paginaAnterior()"
                class="tsi-btn tsi-btn-secondary"
              >
                Anterior
              </button>
              <button
                type="button"
                data-testid="btn-pagina-siguiente"
                [disabled]="!puedeSiguiente || loading"
                (click)="paginaSiguiente()"
                class="tsi-btn tsi-btn-primary"
              >
                Siguiente
              </button>
            </div>
          </div>
        }
      </section>

      <section class="space-y-4 tsi-panel p-6">
        <button
          type="button"
          class="flex w-full items-center justify-between text-left"
          (click)="loteAbierto = !loteAbierto"
          [attr.aria-expanded]="loteAbierto"
        >
          <h2 class="tsi-display text-lg font-semibold text-text-primary">Importación en lote (CSV)</h2>
          <app-tabler-icon [name]="loteAbierto ? 'chevron-up' : 'chevron-down'" [size]="20" />
        </button>
        @if (loteAbierto) {
          <p class="text-sm text-text-secondary">
            La importación es <strong>todo-o-nada</strong>: si una fila falla, no se inserta
            ninguna. Descarga la plantilla para partir de un archivo válido.
          </p>

          <div class="overflow-x-auto">
            <table class="w-full min-w-[34rem] border-collapse text-left text-xs">
              <thead>
                <tr class="border-b border-border-default text-text-secondary">
                  <th class="py-2 pr-4 font-medium">Columna</th>
                  <th class="py-2 pr-4 font-medium">¿Obligatoria?</th>
                  <th class="py-2 font-medium">Valores admitidos</th>
                </tr>
              </thead>
              <tbody>
                @for (c of csvColumnas; track c.nombre) {
                  <tr class="border-b border-border-default/50">
                    <td class="py-2 pr-4">
                      <code class="rounded bg-bg-muted px-1">{{ c.nombre }}</code>
                    </td>
                    <td class="py-2 pr-4 text-text-secondary">{{ c.obligatoria }}</td>
                    <td class="py-2 text-text-secondary">{{ c.admite }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <button
              type="button"
              (click)="descargarPlantillaCsv()"
              data-testid="btn-plantilla-csv"
              class="tsi-btn tsi-btn-secondary"
            >
              <app-tabler-icon name="download" [size]="16" />
              Descargar plantilla
            </button>
            <button
              type="button"
              (click)="exportarCatalogoCsv()"
              data-testid="btn-exportar-csv"
              class="tsi-btn tsi-btn-secondary"
            >
              <app-tabler-icon name="download" [size]="16" />
              Exportar catálogo
            </button>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <input
              type="file"
              accept=".csv"
              (change)="onArchivoSeleccionado($event)"
              class="tsi-input"
            />
            <button
              type="button"
              [disabled]="!archivoSeleccionado || importando"
              (click)="importarLote()"
              class="tsi-btn tsi-btn-primary"
            >
              {{ importando ? 'Importando…' : 'Importar' }}
            </button>
          </div>
          @if (loteResultado) {
            <p class="text-sm text-text-primary">
              {{ loteResultado.insertadas }} insertadas
              @if (loteResultado.usuarios_creados != null) {
                ({{ loteResultado.usuarios_creados }} usuarios)
              }
            </p>
            @if (loteResultado.fallidas.length > 0) {
              <ul class="list-inside list-disc text-sm text-alert-critical">
                @for (fallida of loteResultado.fallidas; track fallida.fila) {
                  <li>Fila {{ fallida.fila }}: {{ fallida.motivo }}</li>
                }
              </ul>
            }
          }
          @if (loteError) {
            <p class="text-sm text-alert-critical">{{ loteError }}</p>
          }
        }
      </section>
    </div>

    @if (bajaDialog) {
      <div
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
        role="dialog"
        aria-modal="true"
        data-testid="baja-dialog"
      >
        <div class="w-full max-w-md space-y-4 rounded-xl bg-bg-surface p-6 shadow-lg">
          @if (bajaDialog.step === 1) {
            <h3 class="tsi-display text-lg font-semibold text-text-primary">Dar de baja</h3>
            <p class="text-sm text-text-secondary">
              Unidad #{{ bajaDialog.idunidademergencia }} ({{ bajaDialog.placa }}). Indica el motivo.
            </p>
            <label class="block">
              <span class="mb-1 block text-sm font-medium text-text-secondary">Motivo</span>
              <input
                [(ngModel)]="bajaDialog.motivo"
                name="motivoBaja"
                class="tsi-input w-full"
          placeholder="Motivo, en una frase"
        />
            </label>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                (click)="bajaDialog = null"
                class="tsi-btn tsi-btn-primary"
              >
                Cancelar
              </button>
              <button
                type="button"
                (click)="bajaPaso2()"
                class="tsi-btn border border-alert-critical bg-transparent text-alert-critical hover:bg-alert-critical-bg"
              >
                Continuar
              </button>
            </div>
          } @else if (bajaDialog.step === 2) {
            <h3 class="tsi-display text-lg font-semibold text-text-primary">Confirmar baja</h3>
            <p class="text-sm text-text-secondary">
              ¿Confirmas dar de baja la unidad #{{ bajaDialog.idunidademergencia }}
              ({{ bajaDialog.placa }})? Motivo: {{ bajaDialog.motivo }}
            </p>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                (click)="bajaDialog = null"
                class="tsi-btn tsi-btn-primary"
              >
                Cancelar
              </button>
              <button
                type="button"
                (click)="confirmarBaja(false)"
                [disabled]="bajaProcesando"
                class="tsi-btn border border-alert-critical bg-transparent text-alert-critical hover:bg-alert-critical-bg"
              >
                {{ bajaProcesando ? 'Procesando…' : 'Dar de baja' }}
              </button>
            </div>
          } @else {
            <h3 class="tsi-display text-lg font-semibold text-text-primary">Despacho activo</h3>
            <p class="text-sm text-text-secondary">
              La unidad tiene un despacho en curso. ¿Forzar la baja de todas formas?
            </p>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                (click)="bajaDialog = null"
                class="tsi-btn tsi-btn-primary"
              >
                Cancelar
              </button>
              <button
                type="button"
                (click)="confirmarBaja(true)"
                [disabled]="bajaProcesando"
                class="tsi-btn border border-alert-critical bg-transparent text-alert-critical hover:bg-alert-critical-bg"
              >
                Forzar baja
              </button>
            </div>
          }
        </div>
      </div>
    }

    @if (reactivarDialog) {
      <div
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
        role="dialog"
        aria-modal="true"
        data-testid="reactivar-dialog"
      >
        <div class="w-full max-w-md space-y-4 rounded-xl bg-bg-surface p-6 shadow-lg">
          @if (reactivarDialog.step === 1) {
            <h3 class="tsi-display text-lg font-semibold text-text-primary">Reactivar unidad</h3>
            <p class="text-sm text-text-secondary">
              ¿Deseas reactivar #{{ reactivarDialog.idunidademergencia }}
              ({{ reactivarDialog.placa }})?
            </p>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                (click)="reactivarDialog = null"
                class="tsi-btn tsi-btn-secondary"
              >
                Cancelar
              </button>
              <button
                type="button"
                (click)="reactivarDialog.step = 2"
                class="tsi-btn tsi-btn-primary"
              >
                Continuar
              </button>
            </div>
          } @else {
            <h3 class="tsi-display text-lg font-semibold text-text-primary">Confirmar reactivación</h3>
            <p class="text-sm text-text-secondary">
              La unidad volverá a estar operativa en el catálogo.
            </p>
            @if (reactivarError) {
              <p class="text-sm text-alert-critical">{{ reactivarError }}</p>
            }
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                (click)="reactivarDialog = null"
                class="tsi-btn tsi-btn-secondary"
              >
                Cancelar
              </button>
              <button
                type="button"
                (click)="confirmarReactivar()"
                [disabled]="reactivarProcesando"
                class="tsi-btn tsi-btn-primary"
              >
                {{ reactivarProcesando ? 'Procesando…' : 'Reactivar' }}
              </button>
            </div>
          }
        </div>
      </div>
    }
  `,
})
export class CatalogoPage implements OnInit, OnDestroy {
  private readonly facade = inject(UnidadEmergenciaFacadeService);
  private readonly listaSeleccion = inject(ListaSeleccionStorage);
  private readonly notifications = inject(NotificationService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();
  private readonly load$ = new Subject<{ resetCursor: boolean }>();
  private readonly textoFiltro$ = new Subject<string>();

  readonly csvColumnas = CSV_DOCUMENTACION;
  readonly pageLimit = PAGE_LIMIT;
  readonly listTableClass = LIST_TABLE_CLASS;
  readonly listTableThClass = LIST_TABLE_TH_CLASS;
  readonly listTableThRightClass = LIST_TABLE_TH_RIGHT_CLASS;
  readonly listTableTdClass = LIST_TABLE_TD_CLASS;
  readonly listTableTdPrimaryClass = LIST_TABLE_TD_PRIMARY_CLASS;
  readonly listActionIconBtnClass = LIST_ACTION_ICON_BTN_CLASS;
  readonly listFilterControlClass = LIST_FILTER_CONTROL_CLASS;
  readonly listFilterControlClassSelect = LIST_FILTER_SELECT_CLASS;
  readonly tiposUnidad: TipoUnidadEmergencia[] = [
    'Ambulancia',
    'Grúa',
    'Patrulla',
    'Bomberos',
    'Defensa Civil',
  ];

  unidades: UnidadEmergenciaData[] = [];
  unidadesError: string | null = null;
  loading = false;
  selectedId: string | null = null;

  filtroQ = '';
  filtroEstado: EstadoFiltro = 'todas';
  filtroTipo: TipoUnidadEmergencia | '' = '';
  cursor: number | null = null;
  nextCursor: number | null = null;
  /** Stack of cursors for "Anterior" (empty = first page). */
  private cursorStack: number[] = [];

  loteAbierto = false;
  archivoSeleccionado: File | null = null;
  importando = false;
  loteResultado: ImportacionLoteData | null = null;
  loteError: string | null = null;

  bajaDialog: BajaDialogState | null = null;
  bajaProcesando = false;

  reactivarDialog: ReactivarDialogState | null = null;
  reactivarProcesando = false;
  reactivarError: string | null = null;

  get puedeAnterior(): boolean {
    return this.cursorStack.length > 0;
  }

  get puedeSiguiente(): boolean {
    return this.nextCursor != null;
  }

  get tieneFiltros(): boolean {
    return (
      !!this.filtroQ.trim() || this.filtroEstado !== 'todas' || !!this.filtroTipo
    );
  }

  ngOnInit(): void {
    this.loading = true;
    this.selectedId = this.listaSeleccion.get();
    const q = this.route.snapshot.queryParamMap.get('q');
    if (q) {
      this.filtroQ = q;
    }

    this.textoFiltro$
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntil(this.destroy$))
      .subscribe(() => this.cargarUnidades({ resetCursor: true }));

    this.load$
      .pipe(
        switchMap(({ resetCursor }) => {
          if (resetCursor) {
            this.cursor = null;
            this.cursorStack = [];
            this.nextCursor = null;
          }
          this.loading = true;
          this.unidadesError = null;
          this.cdr.markForCheck();
          return this.facade.listar(this.buildQuery()).pipe(
            timeout(LIST_TIMEOUT_MS),
            catchError((err: unknown) =>
              of({
                ok: false as const,
                error:
                  err instanceof TimeoutError
                    ? 'La carga tardó demasiado. Reintenta.'
                    : 'No se pudo cargar el catálogo. Intenta de nuevo.',
              }),
            ),
          );
        }),
        takeUntil(this.destroy$),
      )
      .subscribe((result) => {
        this.loading = false;
        if (result.ok && result.data) {
          this.unidades = result.data.items;
          this.nextCursor = result.data.pagination.next_cursor;
          this.unidadesError = null;
        } else {
          this.nextCursor = null;
          this.unidadesError = result.error ?? 'No se pudo cargar el catálogo';
        }
        // AppShell es OnPush: sin markForCheck la tabla no pinta hasta un clic (Actualizar).
        this.cdr.markForCheck();
      });

    this.cargarUnidades({ resetCursor: true });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  filaClass(id: number): string {
    return this.selectedId === String(id)
      ? `${LIST_ROW_CLASS} bg-accent-primary/[0.08] border-l-4 border-l-accent-primary`
      : LIST_ROW_CLASS;
  }

  cardClass(id: number): string {
    return this.selectedId === String(id)
      ? `${LIST_MOBILE_CARD_CLASS} bg-accent-primary/[0.08] border-l-4 border-l-accent-primary`
      : LIST_MOBILE_CARD_CLASS;
  }

  buildQuery(): CatalogQueryState {
    const query: CatalogQueryState = {
      cursor: this.cursor,
      limit: PAGE_LIMIT,
      q: this.filtroQ.trim() || undefined,
      tipounidademergencia: this.filtroTipo || undefined,
    };
    if (this.filtroEstado === 'activa') {
      query.activo = true;
    } else if (this.filtroEstado === 'baja') {
      query.activo = false;
    }
    return query;
  }

  onFiltroTexto(): void {
    this.textoFiltro$.next(this.filtroQ.trim());
  }

  onFiltroSelect(): void {
    this.cargarUnidades({ resetCursor: true });
  }

  /** @deprecated kept for specs that call onFiltrosChange */
  onFiltrosChange(): void {
    this.cargarUnidades({ resetCursor: true });
  }

  cargarUnidades(opts?: { resetCursor?: boolean }): void {
    this.load$.next({ resetCursor: opts?.resetCursor === true });
  }

  paginaSiguiente(): void {
    if (this.nextCursor == null) return;
    this.cursorStack.push(this.cursor ?? 0);
    this.cursor = this.nextCursor;
    this.cargarUnidades();
  }

  paginaAnterior(): void {
    if (!this.cursorStack.length) return;
    const prev = this.cursorStack.pop()!;
    this.cursor = prev > 0 ? prev : null;
    this.cargarUnidades();
  }

  irNueva(): void {
    void this.router.navigate(['/red-operativa/alta-unidades/nueva']);
  }

  irDetalle(idunidademergencia: number): void {
    this.listaSeleccion.set(String(idunidademergencia));
    this.selectedId = String(idunidademergencia);
    void this.router.navigate(['/red-operativa/alta-unidades/detalle', idunidademergencia]);
  }

  irEditar(idunidademergencia: number): void {
    this.listaSeleccion.set(String(idunidademergencia));
    this.selectedId = String(idunidademergencia);
    void this.router.navigate(['/red-operativa/alta-unidades/editar', idunidademergencia]);
  }

  onArchivoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.archivoSeleccionado = input.files?.[0] ?? null;
  }

  // ── CSV: plantilla y exportación ───────────────────────────────────────────

  /**
   * Descarga una plantilla con la cabecera y **una fila de ejemplo válida**.
   *
   * Una cabecera sola no basta: la importación es todo-o-nada, así que un valor
   * mal escrito —"Grua" por "Grúa"— tumba el archivo entero. Ver un ejemplo
   * correcto evita la mayor parte de esos viajes.
   */
  descargarPlantillaCsv(): void {
    this.descargarCsv(
      [CSV_COLUMNAS.join(','), CSV_EJEMPLO.map(escaparCampoCsv).join(',')].join('\r\n'),
      'plantilla-unidades.csv',
    );
  }

  /**
   * Exporta el catálogo visible con las MISMAS columnas de la plantilla, para
   * que sirva de base de un archivo de importación sin reordenar nada a mano.
   *
   * `gmail` sale en blanco a propósito: el listado no expone el correo de acceso
   * de cada unidad —es credencial, no dato de flota— y el archivo se usa para
   * dar de alta unidades **nuevas**, donde ese correo aún no existe. Las
   * unidades ya registradas no se pueden reimportar de todas formas: su placa
   * está tomada.
   */
  exportarCatalogoCsv(): void {
    if (!this.unidades.length) {
      this.notifications.alert('No hay unidades que exportar.', 'Exportar CSV');
      return;
    }
    const filas = this.unidades.map((u) =>
      [
        u.condado ?? '',
        u.estado ?? '',
        u.tipopropiedad ?? '',
        u.placa ?? '',
        u.contactoproveedor ?? '',
        u.unidademergencia ?? '',
        u.tipounidademergencia ?? '',
        '',
      ]
        .map((v) => escaparCampoCsv(String(v)))
        .join(','),
    );
    this.descargarCsv([CSV_COLUMNAS.join(','), ...filas].join('\r\n'), 'unidades.csv');
  }

  private descargarCsv(contenido: string, nombreArchivo: string): void {
    // BOM UTF-8: sin él Excel abre "Grúa" como "GrÃºa" y el archivo vuelve
    // corrupto en la reimportación.
    const blob = new Blob([`﻿${contenido}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = nombreArchivo;
    enlace.click();
    URL.revokeObjectURL(url);
  }

  importarLote(): void {
    if (!this.archivoSeleccionado) return;
    this.loteError = null;
    this.loteResultado = null;
    this.importando = true;
    this.facade.importarLote(this.archivoSeleccionado).subscribe((result) => {
      this.importando = false;
      if (result.ok && result.data) {
        this.loteResultado = result.data;
        this.cargarUnidades({ resetCursor: true });
      } else {
        this.loteError = result.error ?? 'Error al importar el archivo';
      }
      this.cdr.markForCheck();
    });
  }

  iniciarBaja(u: UnidadEmergenciaData): void {
    this.bajaDialog = {
      step: 1,
      idunidademergencia: u.idunidademergencia,
      placa: u.placa,
      motivo: '',
    };
  }

  bajaPaso2(): void {
    if (!this.bajaDialog) return;
    if (!this.bajaDialog.motivo.trim()) {
      this.notifications.toast('Indica el motivo de la baja.', 'warning');
      return;
    }
    this.bajaDialog = { ...this.bajaDialog, step: 2 };
  }

  confirmarBaja(forzar: boolean): void {
    if (!this.bajaDialog) return;
    this.bajaProcesando = true;
    const { idunidademergencia, motivo } = this.bajaDialog;
    this.facade.darDeBaja(idunidademergencia, motivo, forzar).subscribe((result) => {
      this.bajaProcesando = false;
      if (result.ok) {
        this.notifications.toast('Unidad dada de baja correctamente.', 'success');
        this.bajaDialog = null;
        this.cargarUnidades();
      } else if (!forzar && result.error?.toLowerCase().includes('despacho activo')) {
        this.bajaDialog = { ...this.bajaDialog!, step: 3 };
      } else {
        this.notifications.toast(result.error ?? 'No se pudo dar de baja.', 'critical');
      }
      this.cdr.markForCheck();
    });
  }

  iniciarReactivar(u: UnidadEmergenciaData): void {
    this.reactivarError = null;
    this.reactivarDialog = {
      step: 1,
      idunidademergencia: u.idunidademergencia,
      placa: u.placa,
    };
  }

  confirmarReactivar(): void {
    if (!this.reactivarDialog) return;
    this.reactivarProcesando = true;
    this.reactivarError = null;
    this.facade.reactivar(this.reactivarDialog.idunidademergencia).subscribe((result) => {
      this.reactivarProcesando = false;
      if (result.ok) {
        this.notifications.toast('Unidad reactivada correctamente.', 'success');
        this.reactivarDialog = null;
        this.cargarUnidades();
      } else {
        const err = result.error ?? 'No se pudo reactivar la unidad.';
        this.reactivarError = /placa|409|ya existe|duplicad/i.test(err)
          ? 'No se puede reactivar: esa placa ya está en uso por otra unidad activa.'
          : err;
      }
      this.cdr.markForCheck();
    });
  }
}
