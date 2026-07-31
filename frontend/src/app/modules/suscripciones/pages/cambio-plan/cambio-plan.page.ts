import { CommonModule, CurrencyPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

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
import { Plan, SolicitudCambioPlan } from '../../services/models/suscripciones.types';
import { PlanApiService } from '../../services/plan-api.service';
import { SuscripcionApiService } from '../../services/suscripcion-api.service';
import { billingEstadoBadge } from '../../billing-ui';

@Component({
  selector: 'app-cambio-plan',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CurrencyPipe,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './cambio-plan.page.html',
})
export class CambioPlanPage implements OnInit {
  private readonly api = inject(SuscripcionApiService);
  private readonly plansApi = inject(PlanApiService);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly solicitudes = signal<SolicitudCambioPlan[]>([]);
  readonly planes = signal<Plan[]>([]);
  readonly message = signal<string | null>(null);
  readonly busy = signal(false);

  readonly listTableClass = LIST_TABLE_CLASS;
  readonly listTableThClass = LIST_TABLE_TH_CLASS;
  readonly listTableTdClass = LIST_TABLE_TD_CLASS;
  readonly listTableTdPrimaryClass = LIST_TABLE_TD_PRIMARY_CLASS;
  readonly listRowClass = LIST_ROW_CLASS;
  readonly listMobileCardClass = LIST_MOBILE_CARD_CLASS;

  idplansolicitado: number | null = null;
  motivo = '';

  ngOnInit(): void {
    this.cargar();
    this.plansApi.listar(true).subscribe({
      next: (res) => this.planes.set(res.data ?? []),
    });
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listarSolicitudesCambioPlan({ limit: 20 }).subscribe({
      next: (res) => {
        this.solicitudes.set(res.data ?? []);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Error al cargar solicitudes.');
        this.loading.set(false);
      },
    });
  }

  badge(estado?: string): string {
    return billingEstadoBadge(estado);
  }

  nombrePlan(id?: number): string {
    const p = this.planes().find((x) => x.idplan === id);
    return p?.nombre ?? `#${id}`;
  }

  solicitar(): void {
    if (!this.idplansolicitado) return;
    this.busy.set(true);
    this.message.set(null);
    this.api
      .solicitarCambioPlan(
        { idplansolicitado: this.idplansolicitado, motivo: this.motivo || 'Solicitud desde portal' },
        crypto.randomUUID(),
      )
      .subscribe({
        next: (res) => {
          const est = res.data?.estado;
          this.message.set(
            est === 'Aprobada'
              ? 'Upgrade aplicado automáticamente.'
              : 'Solicitud enviada. Un administrador debe aprobar el downgrade.',
          );
          this.busy.set(false);
          this.cargar();
        },
        error: (err) => {
          this.message.set(err?.error?.detail ?? 'No se pudo crear la solicitud.');
          this.busy.set(false);
        },
      });
  }
}
