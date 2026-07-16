import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { DisponibilidadUnidadApiService } from '../../services/disponibilidad-unidad-api.service';
import {
  DisponibilidadUnidadData,
  EstadoDisponibilidadUnidad,
} from '../../services/models/evidencia-unidad.types';

@Component({
  selector: 'app-panel-disponibilidad',
  standalone: true,
  imports: [FormsModule, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './panel-disponibilidad.page.html',
})
export class PanelDisponibilidadPage {
  private readonly disponibilidadApi = inject(DisponibilidadUnidadApiService);
  private readonly notifications = inject(NotificationService);

  readonly estados: EstadoDisponibilidadUnidad[] = ['Activa', 'Ocupada', 'Fuera de servicio'];
  estadoSeleccionado: EstadoDisponibilidadUnidad = 'Activa';
  readonly disponibilidad = signal<DisponibilidadUnidadData | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly cargando = signal(false);

  constructor() {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.disponibilidadApi.consultarMiDisponibilidad().subscribe({
      next: (res) => {
        this.disponibilidad.set(res.data);
        this.estadoSeleccionado = res.data.estado_actual;
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudo consultar la disponibilidad.');
        this.loading.set(false);
      },
    });
  }

  declararEstado(): void {
    this.cargando.set(true);
    this.disponibilidadApi.declararMiEstado({ estadonuevo: this.estadoSeleccionado }).subscribe({
      next: (res) => {
        this.cargando.set(false);
        this.notifications.toast(`Estado actualizado a ${res.data.estadonuevo}.`, 'success');
        this.cargar();
      },
      error: () => {
        this.cargando.set(false);
        this.notifications.alert('No se pudo declarar el nuevo estado.', 'Error al actualizar');
      },
    });
  }
}
