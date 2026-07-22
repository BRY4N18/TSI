import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { DisponibilidadUnidadApiService } from '../../services/disponibilidad-unidad-api.service';
import {
  DisponibilidadUnidadData,
  EstadoDisponibilidadUnidadSeleccionable,
  HistorialEstadoUnidadItem,
} from '../../services/models/evidencia-unidad.types';

const ESTADOS_SELECCIONABLES: EstadoDisponibilidadUnidadSeleccionable[] = [
  'Activa',
  'Ocupada',
  'Fuera de servicio',
];

@Component({
  selector: 'app-panel-disponibilidad',
  standalone: true,
  imports: [FormsModule, TablerIconComponent, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './panel-disponibilidad.page.html',
})
export class PanelDisponibilidadPage {
  private readonly disponibilidadApi = inject(DisponibilidadUnidadApiService);
  private readonly notifications = inject(NotificationService);

  readonly estados = ESTADOS_SELECCIONABLES;
  estadoSeleccionado: EstadoDisponibilidadUnidadSeleccionable = 'Activa';
  readonly disponibilidad = signal<DisponibilidadUnidadData | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly cargando = signal(false);

  readonly historial = signal<HistorialEstadoUnidadItem[]>([]);
  readonly historialLoading = signal(false);
  readonly historialError = signal<string | null>(null);

  constructor() {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.disponibilidadApi.consultarMiDisponibilidad().subscribe({
      next: (res) => {
        this.disponibilidad.set(res.data);
        this.estadoSeleccionado = (ESTADOS_SELECCIONABLES as string[]).includes(
          res.data.estado_actual,
        )
          ? (res.data.estado_actual as EstadoDisponibilidadUnidadSeleccionable)
          : 'Activa';
        this.loading.set(false);
        this.cargarHistorial(res.data.idunidademergencia);
      },
      error: () => {
        this.error.set('No se pudo consultar la disponibilidad.');
        this.loading.set(false);
      },
    });
  }

  cargarHistorial(idunidademergencia: number): void {
    this.historialLoading.set(true);
    this.historialError.set(null);
    this.disponibilidadApi.consultarHistorial(idunidademergencia).subscribe({
      next: (res) => {
        this.historial.set(res.data.items);
        this.historialLoading.set(false);
      },
      error: () => {
        this.historialError.set('No se pudo cargar el historial de cambios.');
        this.historialLoading.set(false);
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
