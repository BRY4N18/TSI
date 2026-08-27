import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
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
import { PlanApiService } from '../../../suscripciones/services/plan-api.service';
import { SlaConfigApiService } from '../../services/sla-config-api.service';
import { SLAConfig } from '../../services/models/soporte.types';

@Component({
  selector: 'app-configuracion-sla',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './configuracion-sla.page.html',
})
export class ConfiguracionSlaPage {
  private readonly api = inject(SlaConfigApiService);
  private readonly planApi = inject(PlanApiService);

  readonly reglas = signal<SLAConfig[]>([]);
  readonly planes = signal<{ idplan: number; nombre: string }[]>([]);
  readonly mensaje = signal('');
  readonly error = signal('');
  readonly cargando = signal(false);
  idplan = 1;
  tipoincidencia = '';
  prioridad = '';
  tiemporespuestamax = 3600;
  tiemporesolucionmax = 86400;

  readonly listTableClass = LIST_TABLE_CLASS;
  readonly listTableThClass = LIST_TABLE_TH_CLASS;
  readonly listTableTdClass = LIST_TABLE_TD_CLASS;
  readonly listTableTdPrimaryClass = LIST_TABLE_TD_PRIMARY_CLASS;
  readonly listRowClass = LIST_ROW_CLASS;
  readonly listMobileCardClass = LIST_MOBILE_CARD_CLASS;

  constructor() {
    this.cargar();
    this.planApi.listar({ limit: 100 }).subscribe({
      next: (res) => {
        this.planes.set(
          (res?.data ?? []).map((p) => ({
            idplan: p.idplan ?? 1,
            nombre: p.nombre ?? `Plan #${p.idplan}`,
          })),
        );
      },
      error: () => {
        // Fallback manejado por nombrePlan
      },
    });
  }

  nombrePlan(idplan: number): string {
    const p = this.planes().find((item) => item.idplan === idplan);
    if (p && p.nombre) {
      return p.nombre;
    }
    const NOMBRES: Record<number, string> = {
      1: 'Básico',
      2: 'Estándar',
      3: 'Empresarial',
      4: 'Premium',
    };
    return NOMBRES[idplan] ?? `Plan #${idplan}`;
  }

  cargar(): void {
    this.cargando.set(true);
    this.error.set('');
    this.api.listar().subscribe({
      next: (res) => {
        this.reglas.set(res.data.items);
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.error.set('No se pudieron cargar las reglas SLA.');
      },
    });
  }

  crear(): void {
    if (!this.tipoincidencia || !this.prioridad) {
      return;
    }
    this.api
      .crear({
        idplan: this.idplan,
        tipoincidencia: this.tipoincidencia,
        prioridad: this.prioridad,
        tiemporespuestamax: this.tiemporespuestamax,
        tiemporesolucionmax: this.tiemporesolucionmax,
      })
      .subscribe({
        next: () => {
          this.mensaje.set('Regla creada');
          this.tipoincidencia = '';
          this.prioridad = '';
          this.cargar();
        },
        error: () => this.mensaje.set('Error al crear la regla'),
      });
  }
}
