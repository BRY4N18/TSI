import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { SlaConfigApiService } from '../../services/sla-config-api.service';
import { SLAConfig } from '../../services/models/soporte.types';

@Component({
  selector: 'app-configuracion-sla',
  standalone: true,
  imports: [FormsModule, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './configuracion-sla.page.html',
})
export class ConfiguracionSlaPage {
  private readonly api = inject(SlaConfigApiService);

  readonly reglas = signal<SLAConfig[]>([]);
  readonly mensaje = signal('');
  readonly cargando = signal(false);
  idplan = 1;
  tipoincidencia = '';
  prioridad = '';
  tiemporespuestamax = 3600;
  tiemporesolucionmax = 86400;

  constructor() {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.api.listar().subscribe({
      next: (res) => {
        this.reglas.set(res.data.items);
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.mensaje.set('No se pudieron cargar las reglas SLA.');
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
