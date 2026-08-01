import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { SEVERIDAD_INFO } from '../../../accidentes/severidad.constants';
import {
  LIST_ACTION_ICON_BTN_CLASS,
  LIST_MOBILE_CARD_CLASS,
  LIST_PAGE_SHELL_CLASS,
  LIST_ROW_CLASS,
  LIST_TABLE_CLASS,
  LIST_TABLE_TD_CLASS,
  LIST_TABLE_TD_PRIMARY_CLASS,
  LIST_TABLE_TH_CLASS,
  LIST_TABLE_TH_RIGHT_CLASS,
} from '../../../../shared/ui/list-states/list-table.styles';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { HistorialEmergenciaItem } from '../../models/seguimiento.types';
import { ExpedienteClienteApiService } from '../../services/expediente-cliente-api.service';

/**
 * Listado de expedientes del cliente (RF-SEG-006).
 *
 * La navegación "Mis expedientes" apuntaba a la página de detalle sin
 * `idaccidente`, así que renderizaba un encabezado vacío y no pedía nada al
 * backend. Esta es la vista de lista que ese enlace prometía; el detalle vive
 * en `expedientes/:idaccidente`.
 */
@Component({
  selector: 'app-lista-expedientes',
  standalone: true,
  imports: [
    DatePipe,
    TablerIconComponent,
    ListEmptyStateComponent,
    ListErrorStateComponent,
    ListLoadingSkeletonComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './lista-expedientes.page.html',
})
export class ListaExpedientesPage implements OnInit {
  private readonly api = inject(ExpedienteClienteApiService);
  private readonly router = inject(Router);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;
  readonly tableClass = LIST_TABLE_CLASS;
  readonly thClass = LIST_TABLE_TH_CLASS;
  readonly thRightClass = LIST_TABLE_TH_RIGHT_CLASS;
  readonly tdClass = LIST_TABLE_TD_CLASS;
  readonly tdPrimaryClass = LIST_TABLE_TD_PRIMARY_CLASS;
  readonly rowClass = LIST_ROW_CLASS;
  readonly actionBtnClass = LIST_ACTION_ICON_BTN_CLASS;
  readonly mobileCardClass = LIST_MOBILE_CARD_CLASS;

  readonly expedientes = signal<HistorialEmergenciaItem[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly nextCursor = signal<string | null>(null);

  readonly pageLimit = 20;
  cursor: string | null = null;
  private cursorStack: (string | null)[] = [];

  ngOnInit(): void {
    this.cargar();
  }

  get puedeSiguiente(): boolean {
    return this.nextCursor() !== null;
  }

  get puedeAnterior(): boolean {
    return this.cursorStack.length > 0;
  }

  paginaSiguiente(): void {
    const siguiente = this.nextCursor();
    if (!siguiente) {
      return;
    }
    this.cursorStack.push(this.cursor);
    this.cursor = siguiente;
    this.cargar();
  }

  paginaAnterior(): void {
    if (!this.cursorStack.length) {
      return;
    }
    this.cursor = this.cursorStack.pop() ?? null;
    this.cargar();
  }

  severidadLabel(idseveridad: number): string {
    return SEVERIDAD_INFO[idseveridad]?.label ?? '—';
  }

  verDetalle(idaccidente: string): void {
    void this.router.navigate(['/seguimiento/expedientes', idaccidente]);
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);

    this.api.listar({ limit: this.pageLimit, cursor: this.cursor ?? undefined }).subscribe({
      next: (res) => {
        this.expedientes.set(res.data.items ?? []);
        this.nextCursor.set(res.data.next_cursor ?? null);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar tus expedientes.');
        this.loading.set(false);
      },
    });
  }
}
