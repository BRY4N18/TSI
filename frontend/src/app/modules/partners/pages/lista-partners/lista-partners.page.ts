import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

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
import { ESTADOS_PARTNER, presentacionDe } from '../../estado-partner.constants';
import { PartnerApiService } from '../../services/partner-api.service';
import { formatearCupo, formatearPlan } from '../../services/models/centinelas';
import type { EstadoPartner, PartnerListItem } from '../../services/models/partner.types';

const CLAVE_ULTIMO_ABIERTO = 'tsi.partners.ultimo-abierto';

/**
 * Lista de partners — punto de entrada de la consola (FR-UI-001/002/003).
 *
 * VARIANTE VER-ONLY del design-system: la única acción es `eye`. No hay
 * `pencil` porque el backend no expone PATCH de ficha de partner, y el propio
 * design-system prohíbe mostrarlo deshabilitado: no se expone lo que el rol
 * (o el sistema) no puede hacer.
 */
@Component({
  selector: 'app-lista-partners',
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
      <header class="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="m-0 text-2xl font-bold text-text-primary">Partners</h1>
          <p class="mt-1 text-sm text-text-secondary">
            Incorporar partners y asignarles su plan de acceso
          </p>
        </div>
        <a
          routerLink="/partners/consola/nuevo"
          data-testid="btn-registrar-partner"
          class="inline-flex items-center gap-2 rounded-lg bg-accent-primary px-5 py-2.5 text-sm font-medium text-white hover:bg-accent-hover"
        >
          <app-tabler-icon name="plus" [size]="18" />
          Registrar partner
        </a>
      </header>

      <div class="mb-4 max-w-xs">
        <label class="mb-1 block text-sm font-medium text-text-secondary" for="filtro-estado">
          Estado
        </label>
        <select
          id="filtro-estado"
          data-testid="filtro-estado"
          [class]="filtroClass"
          [ngModel]="estado()"
          (ngModelChange)="cambiarEstado($event)"
        >
          <option value="">Todos</option>
          @for (e of estados; track e) {
            <option [value]="e">{{ e }}</option>
          }
        </select>
      </div>

      @if (cargando()) {
        <app-list-loading-skeleton [count]="5" />
      } @else if (error()) {
        <app-list-error-state [message]="error()!" (retry)="recargar()" />
      } @else if (partners().length === 0) {
        <app-list-empty-state
          message="Todavía no hay partners registrados."
          icon="license"
        />
      } @else {
        <!-- Desktop / Tablet -->
        <div class="hidden overflow-x-auto md:block">
          <table [class]="tablaClass" data-testid="tabla-partners">
            <thead>
              <tr>
                <th [class]="thClass" scope="col">Partner</th>
                <th [class]="thClass" scope="col">Plan</th>
                <th [class]="thClass" scope="col">Cupo mensual</th>
                <th [class]="thClass" scope="col">Estado</th>
                <th [class]="thRightClass" scope="col">Acciones</th>
              </tr>
            </thead>
            <tbody>
              @for (p of partners(); track p.idpartner) {
                <tr [class]="claseFila(p)" [attr.data-testid]="'fila-' + p.idpartner">
                  <td [class]="tdPrimaryClass">{{ p.nombrepartner }}</td>
                  <td [class]="tdClass">{{ plan(p) }}</td>
                  <td [class]="tdClass">{{ cupo(p) }}</td>
                  <td [class]="tdClass">
                    <span
                      class="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium"
                      [class]="presentacion(p.estado).tono"
                      [attr.data-testid]="'badge-estado-' + p.idpartner"
                    >
                      <app-tabler-icon [name]="presentacion(p.estado).icono" [size]="14" />
                      {{ p.estado }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-right">
                    <!-- Única acción: Ver. Sin lápiz de edición (FR-UI-003). -->
                    <button
                      type="button"
                      [class]="accionClass"
                      [attr.data-testid]="'btn-ver-' + p.idpartner"
                      [attr.aria-label]="'Ver detalles de ' + p.nombrepartner"
                      [title]="'Ver detalles de ' + p.nombrepartner"
                      (click)="abrir(p)"
                    >
                      <app-tabler-icon name="eye" [size]="18" />
                    </button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>

        <!-- Mobile: cada fila como card, sin scroll horizontal -->
        <ul class="grid gap-3 md:hidden">
          @for (p of partners(); track p.idpartner) {
            <li [class]="cardClass" [attr.data-testid]="'card-' + p.idpartner">
              <p class="m-0 font-semibold text-text-primary">{{ p.nombrepartner }}</p>
              <dl class="mt-2 grid grid-cols-2 gap-2 text-sm">
                <dt class="text-text-secondary">Plan</dt>
                <dd class="m-0 text-text-primary">{{ plan(p) }}</dd>
                <dt class="text-text-secondary">Cupo mensual</dt>
                <dd class="m-0 text-text-primary">{{ cupo(p) }}</dd>
                <dt class="text-text-secondary">Estado</dt>
                <dd class="m-0 text-text-primary">{{ p.estado }}</dd>
              </dl>
              <button
                type="button"
                [class]="accionClass"
                [attr.aria-label]="'Ver detalles de ' + p.nombrepartner"
                (click)="abrir(p)"
              >
                <app-tabler-icon name="eye" [size]="18" />
              </button>
            </li>
          }
        </ul>

        @if (siguienteCursor() !== null) {
          <div class="mt-6 grid place-items-center">
            <button
              type="button"
              data-testid="btn-cargar-mas"
              class="rounded-lg border border-accent-primary px-5 py-2.5 text-sm font-medium text-accent-primary hover:bg-bg-surface"
              [disabled]="cargandoMas()"
              (click)="cargarMas()"
            >
              {{ cargandoMas() ? 'Cargando…' : 'Cargar más' }}
            </button>
          </div>
        }
      }
    </section>
  `,
})
export class ListaPartnersPage implements OnInit {
  private readonly api = inject(PartnerApiService);
  private readonly router = inject(Router);

  readonly partners = signal<PartnerListItem[]>([]);
  readonly cargando = signal(true);
  readonly cargandoMas = signal(false);
  readonly error = signal<string | null>(null);
  readonly estado = signal<'' | EstadoPartner>('');
  readonly siguienteCursor = signal<number | null>(null);
  readonly ultimoAbierto = signal<number | null>(null);

  readonly estados = ESTADOS_PARTNER;
  readonly shellClass = LIST_PAGE_SHELL_CLASS;
  readonly tablaClass = LIST_TABLE_CLASS;
  readonly thClass = LIST_TABLE_TH_CLASS;
  readonly thRightClass = LIST_TABLE_TH_RIGHT_CLASS;
  readonly tdClass = LIST_TABLE_TD_CLASS;
  readonly tdPrimaryClass = LIST_TABLE_TD_PRIMARY_CLASS;
  readonly accionClass = LIST_ACTION_ICON_BTN_CLASS;
  readonly cardClass = LIST_MOBILE_CARD_CLASS;
  readonly filtroClass = LIST_FILTER_CONTROL_CLASS;

  ngOnInit(): void {
    this.ultimoAbierto.set(this.leerUltimoAbierto());
    this.recargar();
  }

  presentacion = presentacionDe;

  /** `''` es el centinela de «sin plan»; nunca se muestra crudo. */
  plan(p: PartnerListItem): string {
    return formatearPlan(p.planapi);
  }

  /** `-1` es el centinela de «sin cupo»; mostrarlo sería un defecto visible. */
  cupo(p: PartnerListItem): string {
    return formatearCupo(p.limitellamadasmes);
  }

  /**
   * Marca de orientación del último registro abierto: acento de marca muy
   * tenue, deliberadamente NO un token de severidad — teñir con severidad
   * haría que «esto fue lo último que abriste» se confunda con «esto es grave».
   */
  claseFila(p: PartnerListItem): string {
    const base = LIST_ROW_CLASS;
    return p.idpartner === this.ultimoAbierto()
      ? `${base} bg-accent-primary/[0.07]`
      : base;
  }

  cambiarEstado(valor: '' | EstadoPartner): void {
    this.estado.set(valor);
    this.recargar();
  }

  recargar(): void {
    this.cargando.set(true);
    this.error.set(null);
    this.api.listar({ estado: this.estado() || undefined, limit: 20 }).subscribe({
      next: (res) => {
        this.partners.set(res.data);
        this.siguienteCursor.set(res.meta?.pagination?.next_cursor ?? null);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar el listado de partners.');
        this.cargando.set(false);
      },
    });
  }

  cargarMas(): void {
    const cursor = this.siguienteCursor();
    if (cursor === null) {
      return;
    }
    this.cargandoMas.set(true);
    this.api.listar({ estado: this.estado() || undefined, limit: 20, cursor }).subscribe({
      next: (res) => {
        this.partners.update((actuales) => [...actuales, ...res.data]);
        this.siguienteCursor.set(res.meta?.pagination?.next_cursor ?? null);
        this.cargandoMas.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar la siguiente página.');
        this.cargandoMas.set(false);
      },
    });
  }

  abrir(p: PartnerListItem): void {
    this.guardarUltimoAbierto(p.idpartner);
    void this.router.navigate(['/partners/consola', p.idpartner]);
  }

  private leerUltimoAbierto(): number | null {
    try {
      const crudo = localStorage.getItem(CLAVE_ULTIMO_ABIERTO);
      return crudo ? Number(crudo) : null;
    } catch {
      return null;
    }
  }

  private guardarUltimoAbierto(idpartner: number): void {
    try {
      localStorage.setItem(CLAVE_ULTIMO_ABIERTO, String(idpartner));
    } catch {
      // Sin storage disponible la marca de orientación se pierde; no es motivo
      // para romper la navegación.
    }
  }
}
