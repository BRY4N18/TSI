import { CommonModule, CurrencyPipe, DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';

import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import {
  LIST_MOBILE_CARD_CLASS,
  LIST_ROW_CLASS,
  LIST_TABLE_CLASS,
  LIST_TABLE_TD_CLASS,
  LIST_TABLE_TD_PRIMARY_CLASS,
  LIST_TABLE_TH_CLASS,
} from '../../../../shared/ui/list-states/list-table.styles';
import { Factura } from '../../services/models/suscripciones.types';
import { FacturaApiService } from '../../services/factura-api.service';
import { billingEstadoBadge } from '../../billing-ui';

@Component({
  selector: 'app-historial-facturas',
  standalone: true,
  imports: [
    CommonModule,
    CurrencyPipe,
    DatePipe,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './historial-facturas.page.html',
})
export class HistorialFacturasPage implements OnInit {
  private readonly api = inject(FacturaApiService);

  readonly tableClass = LIST_TABLE_CLASS;
  readonly thClass = LIST_TABLE_TH_CLASS;
  readonly tdClass = LIST_TABLE_TD_CLASS;
  readonly tdPrimaryClass = LIST_TABLE_TD_PRIMARY_CLASS;
  readonly rowClass = LIST_ROW_CLASS;
  readonly mobileCardClass = LIST_MOBILE_CARD_CLASS;

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly items = signal<Factura[]>([]);
  readonly selected = signal<Factura | null>(null);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listar({ limit: 20 }).subscribe({
      next: (res) => {
        this.items.set(res.data ?? []);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Error al cargar facturas.');
        this.loading.set(false);
      },
    });
  }

  badge(estado?: string): string {
    return billingEstadoBadge(estado);
  }

  verDetalle(f: Factura): void {
    if (!f.id_factura) return;
    this.api.obtener(f.id_factura).subscribe({
      next: (res) => this.selected.set(res.data ?? f),
      error: () => this.selected.set(f),
    });
  }
}
