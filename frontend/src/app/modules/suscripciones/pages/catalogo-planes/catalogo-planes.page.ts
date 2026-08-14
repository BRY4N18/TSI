import { CommonModule, CurrencyPipe } from '@angular/common';
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
import {
  catchError,
  debounceTime,
  distinctUntilChanged,
  finalize,
  switchMap,
  takeUntil,
  timeout,
} from 'rxjs/operators';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import {
  LIST_ACTION_ICON_BTN_CLASS,
  LIST_MOBILE_CARD_CLASS,
  LIST_ROW_CLASS,
  LIST_TABLE_CLASS,
  LIST_TABLE_TD_CLASS,
  LIST_TABLE_TD_PRIMARY_CLASS,
  LIST_TABLE_TH_CLASS,
  LIST_TABLE_TH_RIGHT_CLASS,
} from '../../../../shared/ui/list-states/list-table.styles';
import {
  NivelPlan,
  Plan,
  PlanLimites,
  PlanListQuery,
  SeveridadCatalogo,
  SeveridadPlan,
} from '../../services/models/suscripciones.types';
import { PlanApiService } from '../../services/plan-api.service';
import { billingBadge } from '../../billing-ui';

const PAGE_LIMIT = 20;
const LIST_TIMEOUT_MS = 10_000;

type EstadoFiltro = 'todas' | 'activo' | 'inactivo';

@Component({
  selector: 'app-catalogo-planes-suscripciones',
  standalone: true,
  imports: [
    CommonModule,
    CurrencyPipe,
    FormsModule,
    RouterLink,
    TablerIconComponent,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './catalogo-planes.page.html',
})
export class CatalogoPlanesPage implements OnInit, OnDestroy {
  private readonly api = inject(PlanApiService);
  private readonly auth = inject(AuthApiService);
  private readonly notifications = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();
  private readonly load$ = new Subject<{ resetCursor: boolean }>();
  private readonly textoFiltro$ = new Subject<string>();

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
  readonly planes = signal<Plan[]>([]);
  readonly esDirector = signal(false);
  readonly planPendienteDesactivar = signal<Plan | null>(null);
  readonly desactivando = signal(false);
  readonly nextCursor = signal<number | null>(null);
  readonly pageLimit = PAGE_LIMIT;
  /** Catálogo `Dim_Severidad` para traducir los ids que guardan los planes. */
  readonly severidadesCatalogo = signal<SeveridadCatalogo[]>([]);

  filtroQ = '';
  filtroEstado: EstadoFiltro = 'todas';
  filtroNivel: NivelPlan | '' = '';
  cursor: number | null = null;
  private cursorStack: number[] = [];

  readonly niveles: NivelPlan[] = ['Básico', 'Profesional', 'Empresarial'];

  get puedeAnterior(): boolean {
    return this.cursorStack.length > 0;
  }

  get puedeSiguiente(): boolean {
    return this.nextCursor() != null;
  }

  ngOnInit(): void {
    this.api.listarSeveridades().subscribe({
      next: (items) => this.severidadesCatalogo.set(items),
      error: () => this.severidadesCatalogo.set([]),
    });
    this.esDirector.set(this.auth.hasRole('DirectorEstrategia'));
    if (!this.esDirector()) {
      this.filtroEstado = 'activo';
    }

    this.textoFiltro$
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntil(this.destroy$))
      .subscribe(() => this.cargar({ resetCursor: true }));

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
                    'Error al cargar planes.');
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
          this.planes.set([]);
          this.nextCursor.set(null);
          this.error.set(res.__error);
          this.cdr.markForCheck();
          return;
        }
        const envelope = res as {
          data?: Plan[];
          meta?: { pagination?: { next_cursor?: number | string | null } };
        };
        this.planes.set(envelope.data ?? []);
        const raw = envelope.meta?.pagination?.next_cursor;
        if (raw == null || raw === '') {
          this.nextCursor.set(null);
        } else {
          const n = typeof raw === 'string' ? Number(raw) : raw;
          this.nextCursor.set(Number.isFinite(n) ? n : null);
        }
        this.error.set(null);
        this.cdr.markForCheck();
      });

    this.cargar({ resetCursor: true });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  buildQuery(): PlanListQuery {
    const query: PlanListQuery = {
      cursor: this.cursor,
      limit: PAGE_LIMIT,
      q: this.filtroQ.trim() || undefined,
    };
    if (this.filtroNivel) {
      query.nivel = this.filtroNivel;
    }
    if (!this.esDirector()) {
      query.activo = true;
    } else if (this.filtroEstado === 'activo') {
      query.activo = true;
    } else if (this.filtroEstado === 'inactivo') {
      query.activo = false;
    } else {
      // Todas — explícito para no heredar default solo_activos=true del BE
      query.solo_activos = false;
    }
    return query;
  }

  cargar(opts?: { resetCursor?: boolean }): void {
    this.load$.next({ resetCursor: opts?.resetCursor ?? false });
  }

  onFiltroTexto(): void {
    this.textoFiltro$.next(this.filtroQ.trim());
  }

  onFiltroSelect(): void {
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
    this.cursor = prev > 0 ? prev : null;
    this.cargar();
  }

  infoBadge(): string {
    return billingBadge('info');
  }

  okBadge(): string {
    return billingBadge('ok');
  }

  warnBadge(): string {
    return billingBadge('warn');
  }

  pedirDesactivar(plan: Plan): void {
    if (!this.esDirector() || plan.idplan == null) return;
    this.planPendienteDesactivar.set(plan);
  }

  cancelarDesactivar(): void {
    this.planPendienteDesactivar.set(null);
  }

  confirmarDesactivar(): void {
    const plan = this.planPendienteDesactivar();
    if (!this.esDirector() || !plan || plan.idplan == null) return;
    this.desactivando.set(true);
    this.api.actualizar(plan.idplan, { activo: false }, crypto.randomUUID()).subscribe({
      next: () => {
        this.desactivando.set(false);
        this.planPendienteDesactivar.set(null);
        this.notifications.toast(`Plan «${plan.nombre}» desactivado.`, 'success');
        this.cargar();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.desactivando.set(false);
        this.notifications.toast(
          err?.error?.detail ?? 'No se pudo desactivar el plan.',
          'critical',
        );
        this.cdr.markForCheck();
      },
    });
  }

  reactivar(plan: Plan): void {
    if (!this.esDirector() || plan.idplan == null) return;
    this.api.actualizar(plan.idplan, { activo: true }, crypto.randomUUID()).subscribe({
      next: () => {
        this.notifications.toast(`Plan «${plan.nombre}» reactivado.`, 'success');
        this.cargar();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.notifications.toast(
          err?.error?.detail ?? 'No se pudo reactivar el plan.',
          'critical',
        );
        this.cdr.markForCheck();
      },
    });
  }

  limitesTexto(limites?: PlanLimites | string): string {
    if (!limites) return 'Sin límites';
    if (typeof limites === 'string') {
      try {
        return this.limitesTexto(JSON.parse(limites) as PlanLimites);
      } catch {
        return limites;
      }
    }
    // Un plan puede no traer todas las claves de límites (los sembrados de demo
    // solo llevan las de API). Omitimos las ausentes en vez de imprimir
    // `undefined unidades`, que era lo que veía el usuario.
    const partes = [
      limites.unidades_max == null ? null : `${limites.unidades_max} unidades`,
      limites.usuarios_max == null ? null : `${limites.usuarios_max} usuarios`,
      limites.api_calls_mes == null ? null : `${limites.api_calls_mes} API/mes`,
      limites.api_calls_minuto == null ? null : `${limites.api_calls_minuto} API/min`,
    ].filter((p): p is string => p !== null);
    return partes.length ? partes.join(' · ') : 'Sin límites';
  }

  /**
   * Los planes guardan ids de `Dim_Severidad`; la tabla muestra los nombres del
   * catálogo, nunca los identificadores.
   */
  severidadesTexto(severidades?: SeveridadPlan[] | string): string {
    if (!severidades) return 'Sin configurar';
    if (typeof severidades === 'string') {
      try {
        return this.severidadesTexto(JSON.parse(severidades) as SeveridadPlan[]);
      } catch {
        return 'Sin configurar';
      }
    }
    const nombres = this.nombresSeveridad();
    const etiquetas = severidades
      .map((id) => nombres.get(Number(id)))
      .filter((n): n is string => Boolean(n));
    return etiquetas.length ? etiquetas.join(' · ') : 'Sin configurar';
  }

  private nombresSeveridad(): Map<number, string> {
    return new Map(this.severidadesCatalogo().map((s) => [s.idseveridad, s.severidad]));
  }
}
