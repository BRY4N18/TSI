import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
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
import { SlaConfigApiService } from '../../services/sla-config-api.service';
import { SLAConfig } from '../../services/models/soporte.types';

@Component({
  selector: 'app-configuracion-sla',
  standalone: true,
  imports: [
    FormsModule,
    TablerIconComponent,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './configuracion-sla.page.html',
})
export class ConfiguracionSlaPage {
  private readonly api = inject(SlaConfigApiService);

  readonly reglas = signal<SLAConfig[]>([]);
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
