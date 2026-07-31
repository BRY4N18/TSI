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
import { ListaSeleccionStorage } from '../../lista-seleccion.storage';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import {
  CatalogQueryState,
  ImportacionLoteData,
  TipoUnidadEmergencia,
  UnidadEmergenciaData,
} from '../../models/unidad-emergencia.contract';

const CSV_PLANTILLA =
  'idcondado,tipopropiedad,placa,contactoproveedor,unidademergencia,tipounidademergencia,gmail';

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
  imports: [CommonModule, FormsModule, TablerIconComponent],
  template: `
    <div class="mx-auto w-full max-w-5xl space-y-6 p-6">
      <header class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 class="text-[28px] font-bold text-text-primary">Catálogo de unidades</h1>
          <p class="mt-1 text-sm text-text-secondary">
            Flota del Proveedor — ver detalles, crear o editar en páginas dedicadas.
          </p>
        </div>
        <button
          type="button"
          data-testid="btn-nueva-unidad"
          (click)="irNueva()"
          class="inline-flex h-11 items-center gap-2 rounded-md bg-accent-primary px-4 text-sm font-semibold text-white hover:bg-accent-hover"
        >
          <app-tabler-icon name="plus" [size]="18" />
          Nueva unidad
        </button>
      </header>

      <section class="space-y-4 rounded-lg border border-border-default bg-bg-surface p-6">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="text-lg font-semibold text-text-primary">Mis unidades</h2>
          <button
            type="button"
            data-testid="btn-actualizar-lista"
            (click)="cargarUnidades()"
            class="rounded-md border border-accent-primary px-4 py-2 text-sm font-medium text-accent-primary hover:bg-accent-primary/5"
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
              class="w-full rounded-md border border-border-default px-3.5 py-2.5 text-sm text-text-primary focus:border-accent-primary focus:outline-none"
            />
          </label>
          <label class="block">
            <span class="mb-1 block text-xs font-medium text-text-secondary">Estado</span>
            <select
              name="filtroEstado"
              [(ngModel)]="filtroEstado"
              (change)="onFiltroSelect()"
              data-testid="filtro-estado"
              class="w-full rounded-md border border-border-default px-3.5 py-2.5 text-sm text-text-primary focus:border-accent-primary focus:outline-none"
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
              class="w-full rounded-md border border-border-default px-3.5 py-2.5 text-sm text-text-primary focus:border-accent-primary focus:outline-none"
            >
              <option value="">Todos</option>
              @for (t of tiposUnidad; track t) {
                <option [value]="t">{{ t }}</option>
              }
            </select>
          </label>
        </div>

        @if (loading && unidades.length === 0 && !unidadesError) {
          <div class="space-y-2" data-testid="loading-skeleton">
            @for (i of [1, 2, 3]; track i) {
              <div class="h-12 animate-pulse rounded-md bg-bg-page"></div>
            }
          </div>
        } @else if (unidadesError && unidades.length === 0) {
          <div class="space-y-3" role="alert" data-testid="lista-error">
            <p class="text-sm text-alert-critical">{{ unidadesError }}</p>
            <button
              type="button"
              data-testid="btn-reintentar-lista"
              (click)="cargarUnidades()"
              class="rounded-md border border-accent-primary px-4 py-2 text-sm font-medium text-accent-primary"
            >
              Reintentar
            </button>
          </div>
        } @else if (!loading && unidades.length === 0) {
          <div class="space-y-3 py-4 text-center" data-testid="lista-vacia">
            <p class="text-sm text-text-secondary">
              {{
                tieneFiltros
                  ? 'No hay unidades que coincidan con los filtros.'
                  : 'Aún no hay unidades registradas.'
              }}
            </p>
            @if (!tieneFiltros) {
              <button
                type="button"
                (click)="irNueva()"
                class="inline-flex h-11 items-center gap-2 rounded-md bg-accent-primary px-4 text-sm font-semibold text-white hover:bg-accent-hover"
              >
                Nueva unidad
              </button>
            }
          </div>
        } @else {
          <div class="overflow-x-auto rounded-lg border border-border-default">
            <table class="w-full text-left text-sm" data-testid="tabla-unidades">
              <thead class="bg-bg-page">
                <tr>
                  <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">ID</th>
                  <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">Placa</th>
                  <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">Nombre</th>
                  <th class="px-4 py-3 text-xs font-medium uppercase text-text-primary">Estado</th>
                  <th class="px-4 py-3 text-right text-xs font-medium uppercase text-text-primary">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody>
                @for (u of unidades; track u.idunidademergencia) {
                  <tr [class]="filaClass(u.idunidademergencia)">
                    <td class="px-4 py-3 font-mono text-text-primary">
                      {{ u.idunidademergencia }}
                    </td>
                    <td class="px-4 py-3 font-mono text-text-primary">{{ u.placa }}</td>
                    <td class="px-4 py-3 text-text-secondary">{{ u.unidademergencia }}</td>
                    <td class="px-4 py-3">
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
                    <td class="px-4 py-3 text-right">
                      <div class="inline-flex items-center justify-end gap-1">
                        <button
                          type="button"
                          class="inline-flex h-11 w-11 items-center justify-center rounded-md text-text-secondary hover:bg-bg-page hover:text-text-primary"
                          aria-label="Ver detalles"
                          title="Ver detalles"
                          data-testid="btn-ver-detalles"
                          (click)="irDetalle(u.idunidademergencia)"
                        >
                          <app-tabler-icon name="eye" [size]="18" />
                        </button>
                        <button
                          type="button"
                          class="inline-flex h-11 w-11 items-center justify-center rounded-md text-text-secondary hover:bg-bg-page hover:text-text-primary"
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
                class="rounded-md border border-border-default px-4 py-2 text-sm font-medium text-text-primary hover:bg-bg-page disabled:cursor-not-allowed disabled:opacity-40"
              >
                Anterior
              </button>
              <button
                type="button"
                data-testid="btn-pagina-siguiente"
                [disabled]="!puedeSiguiente || loading"
                (click)="paginaSiguiente()"
                class="rounded-md border border-accent-primary px-4 py-2 text-sm font-medium text-accent-primary hover:bg-accent-primary/5 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Siguiente
              </button>
            </div>
          </div>
        }
      </section>

      <section class="space-y-4 rounded-lg border border-border-default bg-bg-surface p-6">
        <button
          type="button"
          class="flex w-full items-center justify-between text-left"
          (click)="loteAbierto = !loteAbierto"
          [attr.aria-expanded]="loteAbierto"
        >
          <h2 class="text-lg font-semibold text-text-primary">Importación en lote (CSV)</h2>
          <app-tabler-icon [name]="loteAbierto ? 'chevron-up' : 'chevron-down'" [size]="20" />
        </button>
        @if (loteAbierto) {
          <p class="text-sm text-text-secondary">
            Columnas:
            <code class="rounded bg-bg-muted px-1 text-xs">{{ csvPlantilla }}</code>. Todo-o-nada.
          </p>
          <div class="flex flex-wrap items-center gap-3">
            <input
              type="file"
              accept=".csv"
              (change)="onArchivoSeleccionado($event)"
              class="text-sm text-text-secondary file:mr-3 file:rounded-md file:border-0 file:bg-accent-primary/10 file:px-3.5 file:py-2 file:text-sm file:font-medium file:text-accent-primary"
            />
            <button
              type="button"
              [disabled]="!archivoSeleccionado || importando"
              (click)="importarLote()"
              class="rounded-md border border-accent-primary px-5 py-2.5 font-medium text-accent-primary hover:bg-accent-primary/5 disabled:cursor-not-allowed disabled:opacity-50"
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
            <h3 class="text-lg font-semibold text-text-primary">Dar de baja</h3>
            <p class="text-sm text-text-secondary">
              Unidad #{{ bajaDialog.idunidademergencia }} ({{ bajaDialog.placa }}). Indica el motivo.
            </p>
            <label class="block">
              <span class="mb-1 block text-sm font-medium text-text-secondary">Motivo</span>
              <input
                [(ngModel)]="bajaDialog.motivo"
                name="motivoBaja"
                class="w-full rounded-md border border-border-default px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none"
              />
            </label>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                (click)="bajaDialog = null"
                class="h-11 rounded-md bg-accent-primary px-4 text-sm font-medium text-white"
              >
                Cancelar
              </button>
              <button
                type="button"
                (click)="bajaPaso2()"
                class="h-11 rounded-md border border-alert-critical px-4 text-sm font-medium text-alert-critical"
              >
                Continuar
              </button>
            </div>
          } @else if (bajaDialog.step === 2) {
            <h3 class="text-lg font-semibold text-text-primary">Confirmar baja</h3>
            <p class="text-sm text-text-secondary">
              ¿Confirmas dar de baja la unidad #{{ bajaDialog.idunidademergencia }}
              ({{ bajaDialog.placa }})? Motivo: {{ bajaDialog.motivo }}
            </p>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                (click)="bajaDialog = null"
                class="h-11 rounded-md bg-accent-primary px-4 text-sm font-medium text-white"
              >
                Cancelar
              </button>
              <button
                type="button"
                (click)="confirmarBaja(false)"
                [disabled]="bajaProcesando"
                class="h-11 rounded-md border border-alert-critical px-4 text-sm font-medium text-alert-critical disabled:opacity-50"
              >
                {{ bajaProcesando ? 'Procesando…' : 'Dar de baja' }}
              </button>
            </div>
          } @else {
            <h3 class="text-lg font-semibold text-text-primary">Despacho activo</h3>
            <p class="text-sm text-text-secondary">
              La unidad tiene un despacho en curso. ¿Forzar la baja de todas formas?
            </p>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                (click)="bajaDialog = null"
                class="h-11 rounded-md bg-accent-primary px-4 text-sm font-medium text-white"
              >
                Cancelar
              </button>
              <button
                type="button"
                (click)="confirmarBaja(true)"
                [disabled]="bajaProcesando"
                class="h-11 rounded-md border border-alert-critical px-4 text-sm font-medium text-alert-critical"
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
            <h3 class="text-lg font-semibold text-text-primary">Reactivar unidad</h3>
            <p class="text-sm text-text-secondary">
              ¿Deseas reactivar #{{ reactivarDialog.idunidademergencia }}
              ({{ reactivarDialog.placa }})?
            </p>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                (click)="reactivarDialog = null"
                class="h-11 rounded-md border border-border-default px-4 text-sm"
              >
                Cancelar
              </button>
              <button
                type="button"
                (click)="reactivarDialog.step = 2"
                class="h-11 rounded-md bg-accent-primary px-4 text-sm font-medium text-white"
              >
                Continuar
              </button>
            </div>
          } @else {
            <h3 class="text-lg font-semibold text-text-primary">Confirmar reactivación</h3>
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
                class="h-11 rounded-md border border-border-default px-4 text-sm"
              >
                Cancelar
              </button>
              <button
                type="button"
                (click)="confirmarReactivar()"
                [disabled]="reactivarProcesando"
                class="h-11 rounded-md bg-accent-primary px-4 text-sm font-medium text-white disabled:opacity-50"
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

  readonly csvPlantilla = CSV_PLANTILLA;
  readonly pageLimit = PAGE_LIMIT;
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
    const base = 'border-t border-border-default';
    return this.selectedId === String(id)
      ? `${base} bg-accent-primary/[0.08] border-l-4 border-l-accent-primary`
      : base;
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
