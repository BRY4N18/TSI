import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Subject, TimeoutError, of } from 'rxjs';
import { catchError, finalize, switchMap, takeUntil, timeout } from 'rxjs/operators';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import {
  LIST_ACTION_ICON_BTN_CLASS,
  LIST_FILTER_CONTROL_CLASS,
  LIST_MOBILE_CARD_CLASS,
  LIST_PAGE_SHELL_CLASS,
  LIST_ROW_CLASS,
  LIST_TABLE_CLASS,
  LIST_TABLE_TD_CLASS,
  LIST_TABLE_TD_PRIMARY_CLASS,
  LIST_TABLE_TH_CLASS,
  LIST_TABLE_TH_RIGHT_CLASS,
} from '../../../../shared/ui/list-states/list-table.styles';
import { crmBadge } from '../../crm-ui';
import { EtapaPipeline, Prospecto, ProspectoListQuery } from '../../models/prospectos.types';
import { ProspectoApiService } from '../../services/prospecto-api.service';

const PAGE_LIMIT = 20;
const LIST_TIMEOUT_MS = 10_000;

type EstadoFiltro = 'todas' | 'activo' | 'inactivo';

@Component({
  selector: 'app-listado-prospectos',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TablerIconComponent,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div [class]="pageShell">
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 class="m-0 text-2xl font-bold text-text-primary">Prospectos</h1>
          <p class="m-0 mt-1 text-sm text-text-secondary">
            Hasta {{ pageLimit }} por página · abrir solo con el ícono de ver
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <button
            type="button"
            data-testid="btn-actualizar-prospectos"
            class="inline-flex items-center gap-2 rounded-md border border-border-default bg-bg-surface px-4 py-2.5 text-sm font-semibold text-text-primary hover:bg-bg-page"
            (click)="cargar()"
          >
            <app-tabler-icon name="refresh" [size]="16" />
            Actualizar
          </button>
          @if (esAdmin()) {
            <a
              routerLink="/ventas-crm/entrada-directa"
              data-testid="btn-entrada-directa"
              class="inline-flex items-center gap-2 rounded-md bg-accent-primary px-4 py-2.5 text-sm font-semibold text-white no-underline [&:hover:not(:disabled)]:bg-accent-hover"
            >
              Entrada directa
            </a>
          }
        </div>
      </div>

      <form
        data-testid="listado-prospectos-filtros"
        class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
      >
        <div class="grid gap-1.5">
          <label for="filtroEstado" class="text-sm font-medium text-text-secondary">Estado</label>
          <select
            id="filtroEstado"
            name="filtroEstado"
            [(ngModel)]="filtroEstado"
            (ngModelChange)="onFiltroChange()"
            data-testid="filtro-activo"
            [class]="filterControl"
          >
            <option value="todas">Todas</option>
            <option value="activo">Activo</option>
            <option value="inactivo">Inactivo</option>
          </select>
        </div>
        <div class="grid gap-1.5">
          <label for="filtroEtapa" class="text-sm font-medium text-text-secondary">Etapa</label>
          <select
            id="filtroEtapa"
            name="filtroEtapa"
            [(ngModel)]="filtroEtapa"
            (ngModelChange)="onFiltroChange()"
            data-testid="filtro-etapa"
            [class]="filterControl"
          >
            <option value="">Todas</option>
            @for (e of etapas; track e) {
              <option [value]="e">{{ e }}</option>
            }
          </select>
        </div>
      </form>

      @if (loading()) {
        <app-list-loading-skeleton />
      } @else if (error()) {
        <app-list-error-state [message]="error()!" (retry)="cargar()" />
      } @else if (items().length === 0) {
        <app-list-empty-state message="No hay prospectos que coincidan con los filtros." icon="list" />
      } @else {
        <table [class]="tableClass">
          <thead>
            <tr class="bg-bg-surface">
              <th [class]="thClass">Nombre</th>
              <th [class]="thClass">Empresa</th>
              <th [class]="thClass">Etapa</th>
              <th [class]="thClass">Estado</th>
              <th [class]="thRightClass">Acciones</th>
            </tr>
          </thead>
          <tbody>
            @for (p of items(); track p.idprospecto) {
              <tr [class]="rowClass">
                <td [class]="tdPrimaryClass">{{ p.nombres }} {{ p.apellidos }}</td>
                <td [class]="tdClass">{{ p.empresa }}</td>
                <td class="px-4 py-3">
                  <span [class]="etapaBadge(p.etapa_actual)">{{ p.etapa_actual }}</span>
                </td>
                <td class="px-4 py-3">
                  <span [class]="p.activo ? okBadge() : warnBadge()">
                    {{ p.activo ? 'Activo' : 'Inactivo' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right">
                  <a
                    [routerLink]="['/ventas-crm/prospectos', p.idprospecto]"
                    data-testid="btn-ver-prospecto"
                    [class]="actionBtnClass + ' no-underline'"
                    aria-label="Ver detalles"
                    title="Ver detalles"
                  >
                    <app-tabler-icon name="eye" [size]="18" />
                  </a>
                </td>
              </tr>
            }
          </tbody>
        </table>

        <div
          class="hidden items-center justify-between px-1 py-3 text-sm text-text-secondary md:flex"
          data-testid="listado-prospectos-pager"
        >
          <span>{{ items().length }} de hasta {{ pageLimit }} en esta página</span>
          <div class="flex gap-2">
            <button
              type="button"
              data-testid="btn-pagina-anterior"
              class="inline-flex min-h-11 items-center justify-center rounded-md border border-border-default px-4 text-sm font-medium text-text-primary hover:bg-bg-page disabled:cursor-not-allowed disabled:opacity-40"
              [disabled]="!puedeAnterior"
              (click)="paginaAnterior()"
            >
              Anterior
            </button>
            <button
              type="button"
              data-testid="btn-pagina-siguiente"
              class="inline-flex min-h-11 items-center justify-center rounded-md border border-accent-primary px-4 text-sm font-medium text-accent-primary hover:bg-accent-primary/5 disabled:cursor-not-allowed disabled:opacity-40"
              [disabled]="!puedeSiguiente"
              (click)="paginaSiguiente()"
            >
              Siguiente
            </button>
          </div>
        </div>

        <div class="grid gap-3 md:hidden">
          @for (p of items(); track p.idprospecto) {
            <div [class]="mobileCardClass">
              <div class="mb-2 flex items-center justify-between gap-2">
                <span class="text-sm font-semibold text-text-primary"
                  >{{ p.nombres }} {{ p.apellidos }}</span
                >
                <a
                  [routerLink]="['/ventas-crm/prospectos', p.idprospecto]"
                  data-testid="btn-ver-prospecto"
                  [class]="actionBtnClass + ' no-underline'"
                  aria-label="Ver detalles"
                  title="Ver detalles"
                >
                  <app-tabler-icon name="eye" [size]="18" />
                </a>
              </div>
              <dl class="grid gap-1 text-sm">
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Empresa</dt>
                  <dd class="truncate font-medium text-text-primary">{{ p.empresa }}</dd>
                </div>
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Etapa</dt>
                  <dd class="font-medium text-text-primary">{{ p.etapa_actual }}</dd>
                </div>
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Estado</dt>
                  <dd class="font-medium text-text-primary">
                    {{ p.activo ? 'Activo' : 'Inactivo' }}
                  </dd>
                </div>
              </dl>
            </div>
          }
          <div class="flex justify-between gap-2 pt-1" data-testid="listado-prospectos-pager-mobile">
            <button
              type="button"
              class="inline-flex min-h-11 flex-1 items-center justify-center rounded-md border border-border-default px-4 text-sm font-medium disabled:opacity-40"
              [disabled]="!puedeAnterior"
              (click)="paginaAnterior()"
            >
              Anterior
            </button>
            <button
              type="button"
              class="inline-flex min-h-11 flex-1 items-center justify-center rounded-md border border-accent-primary px-4 text-sm font-medium text-accent-primary disabled:opacity-40"
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
export class ListadoProspectosPage implements OnInit, OnDestroy {
  private readonly api = inject(ProspectoApiService);
  private readonly auth = inject(AuthApiService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();
  private readonly load$ = new Subject<{ resetCursor: boolean }>();

  readonly pageShell = LIST_PAGE_SHELL_CLASS;
  readonly filterControl = LIST_FILTER_CONTROL_CLASS;
  readonly tableClass = LIST_TABLE_CLASS;
  readonly thClass = LIST_TABLE_TH_CLASS;
  readonly thRightClass = LIST_TABLE_TH_RIGHT_CLASS;
  readonly tdClass = LIST_TABLE_TD_CLASS;
  readonly tdPrimaryClass = LIST_TABLE_TD_PRIMARY_CLASS;
  readonly rowClass = LIST_ROW_CLASS;
  readonly actionBtnClass = LIST_ACTION_ICON_BTN_CLASS;
  readonly mobileCardClass = LIST_MOBILE_CARD_CLASS;

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly items = signal<Prospecto[]>([]);
  readonly esAdmin = signal(false);
  readonly nextCursor = signal<string | number | null>(null);
  readonly pageLimit = PAGE_LIMIT;

  filtroEstado: EstadoFiltro = 'todas';
  filtroEtapa: EtapaPipeline | '' = '';
  cursor: string | number | null = null;
  private cursorStack: Array<string | number> = [];

  readonly etapas: EtapaPipeline[] = [
    'Nuevo',
    'Contactado',
    'Calificado',
    'Propuesta',
    'Negociación',
    'Ganado',
    'Perdido',
  ];

  get puedeAnterior(): boolean {
    return this.cursorStack.length > 0;
  }

  get puedeSiguiente(): boolean {
    return this.nextCursor() != null;
  }

  ngOnInit(): void {
    this.esAdmin.set(this.auth.hasRole('Administrador'));

    this.load$
      .pipe(
        switchMap(({ resetCursor }) => {
          if (resetCursor) {
            this.cursor = null;
            this.cursorStack = [];
            this.nextCursor.set(null);
          }
          this.loading.set(true);
          this.error.set(null);
          this.cdr.markForCheck();
          return this.api.listar(this.buildQuery()).pipe(
            timeout(LIST_TIMEOUT_MS),
            catchError((err: unknown) => {
              const detail =
                err instanceof TimeoutError
                  ? 'La carga tardó demasiado. Reintenta.'
                  : ((err as { error?: { detail?: string } })?.error?.detail ??
                    'Error al cargar prospectos.');
              return of({ __error: detail as string });
            }),
            finalize(() => {
              this.loading.set(false);
              this.cdr.markForCheck();
            }),
          );
        }),
        takeUntil(this.destroy$),
      )
      .subscribe((res) => {
        if (res && '__error' in res) {
          this.items.set([]);
          this.nextCursor.set(null);
          this.error.set(res.__error);
          this.cdr.markForCheck();
          return;
        }
        const envelope = res as {
          data?: Prospecto[];
          meta?: { pagination?: { next_cursor?: string | number | null } };
        };
        this.items.set(envelope.data ?? []);
        const raw = envelope.meta?.pagination?.next_cursor;
        this.nextCursor.set(raw == null || raw === '' ? null : raw);
        this.error.set(null);
        this.cdr.markForCheck();
      });

    this.cargar({ resetCursor: true });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  buildQuery(): ProspectoListQuery {
    const query: ProspectoListQuery = {
      cursor: this.cursor,
      limit: PAGE_LIMIT,
    };
    if (this.filtroEstado === 'activo') query.activo = true;
    else if (this.filtroEstado === 'inactivo') query.activo = false;
    if (this.filtroEtapa) query.etapa_actual = this.filtroEtapa;
    return query;
  }

  cargar(opts?: { resetCursor?: boolean }): void {
    this.load$.next({ resetCursor: opts?.resetCursor ?? false });
  }

  onFiltroChange(): void {
    this.cargar({ resetCursor: true });
  }

  paginaSiguiente(): void {
    const next = this.nextCursor();
    if (next == null) return;
    this.cursorStack.push(this.cursor ?? 0);
    this.cursor = next;
    this.cargar();
  }

  paginaAnterior(): void {
    if (!this.cursorStack.length) return;
    const prev = this.cursorStack.pop()!;
    this.cursor = prev === 0 || prev === '0' ? null : prev;
    this.cargar();
  }

  etapaBadge(etapa: string): string {
    if (etapa === 'Perdido') return crmBadge('danger');
    if (etapa === 'Ganado') return crmBadge('ok');
    if (etapa === 'Negociación' || etapa === 'Propuesta') return crmBadge('warn');
    return crmBadge('info');
  }

  okBadge(): string {
    return crmBadge('ok');
  }

  warnBadge(): string {
    return crmBadge('warn');
  }
}
