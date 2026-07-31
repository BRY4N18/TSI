import { CommonModule, DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';

import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import {
  LIST_MOBILE_CARD_CLASS,
  LIST_PAGE_SHELL_CLASS,
  LIST_ROW_CLASS,
  LIST_TABLE_CLASS,
  LIST_TABLE_TD_CLASS,
  LIST_TABLE_TD_PRIMARY_CLASS,
  LIST_TABLE_TH_CLASS,
} from '../../../../shared/ui/list-states/list-table.styles';
import { NotificacionVentas } from '../../models/notificacion-ventas.types';
import { NotificacionApiService } from '../../services/notificacion-api.service';

@Component({
  selector: 'app-notificaciones-ventas',
  standalone: true,
  imports: [
    CommonModule,
    DatePipe,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div [class]="pageShell">
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 class="m-0 text-2xl font-bold text-text-primary">Notificaciones de ventas</h1>
          <p class="m-0 mt-1 text-sm text-text-secondary">
            Alertas enviadas a gerentes por reglas de comportamiento del prospecto
          </p>
        </div>
        <button
          type="button"
          data-testid="btn-actualizar-notificaciones"
          class="inline-flex min-h-11 items-center justify-center rounded-md border border-border-default bg-bg-surface px-4 text-sm font-medium text-text-primary hover:bg-bg-page"
          (click)="cargar()"
        >
          Actualizar
        </button>
      </div>

      @if (loading()) {
        <app-list-loading-skeleton />
      } @else if (error()) {
        <app-list-error-state [message]="error()!" (retry)="cargar()" />
      } @else if (items().length === 0) {
        <app-list-empty-state message="No hay notificaciones todavía." icon="bell" />
      } @else {
        <table [class]="tableClass">
          <thead>
            <tr class="bg-bg-surface">
              <th [class]="thClass">ID</th>
              <th [class]="thClass">Prospecto</th>
              <th [class]="thClass">Regla</th>
              <th [class]="thClass">Canal</th>
              <th [class]="thClass">Fecha/Hora</th>
            </tr>
          </thead>
          <tbody>
            @for (n of items(); track n.idnotificacion) {
              <tr [class]="rowClass">
                <td [class]="tdPrimaryClass">{{ n.idnotificacion }}</td>
                <td [class]="tdClass">{{ n.id_prospecto }}</td>
                <td [class]="tdClass">{{ n.regladisparada }}</td>
                <td [class]="tdClass">{{ n.canal }}</td>
                <td [class]="tdClass">{{ n.fechahoranotificacion * 1000 | date: 'dd/MM/yyyy HH:mm' }}</td>
              </tr>
            }
          </tbody>
        </table>

        <div class="grid gap-3 md:hidden">
          @for (n of items(); track n.idnotificacion) {
            <div [class]="mobileCardClass">
              <div class="mb-2 flex items-center justify-between gap-2">
                <span class="text-sm font-semibold text-text-primary">#{{ n.idnotificacion }}</span>
                <span class="text-xs text-text-secondary">{{ n.canal }}</span>
              </div>
              <dl class="grid gap-1 text-sm">
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Prospecto</dt>
                  <dd class="font-medium text-text-primary">{{ n.id_prospecto }}</dd>
                </div>
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Regla</dt>
                  <dd class="truncate font-medium text-text-primary">{{ n.regladisparada }}</dd>
                </div>
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Fecha/Hora</dt>
                  <dd class="font-medium text-text-primary">
                    {{ n.fechahoranotificacion * 1000 | date: 'dd/MM/yyyy HH:mm' }}
                  </dd>
                </div>
              </dl>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class NotificacionesVentasPage implements OnInit {
  private readonly api = inject(NotificacionApiService);

  readonly pageShell = LIST_PAGE_SHELL_CLASS;
  readonly tableClass = LIST_TABLE_CLASS;
  readonly thClass = LIST_TABLE_TH_CLASS;
  readonly tdClass = LIST_TABLE_TD_CLASS;
  readonly tdPrimaryClass = LIST_TABLE_TD_PRIMARY_CLASS;
  readonly rowClass = LIST_ROW_CLASS;
  readonly mobileCardClass = LIST_MOBILE_CARD_CLASS;

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly items = signal<NotificacionVentas[]>([]);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listar({ limit: 50 }).subscribe({
      next: (res) => {
        this.items.set(res.data ?? []);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Error al cargar notificaciones');
        this.loading.set(false);
      },
    });
  }
}
