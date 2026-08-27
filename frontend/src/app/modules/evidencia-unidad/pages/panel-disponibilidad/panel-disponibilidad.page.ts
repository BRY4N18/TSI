import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { DisponibilidadUnidadApiService } from '../../services/disponibilidad-unidad-api.service';
import {
  DisponibilidadUnidadData,
  EstadoDisponibilidadUnidadSeleccionable,
  HistorialDespachoUnidadItem,
  HistorialEstadoUnidadItem,
} from '../../services/models/evidencia-unidad.types';

const ESTADOS_SELECCIONABLES: EstadoDisponibilidadUnidadSeleccionable[] = [
  'Activa',
  'Ocupada',
  'Fuera de servicio',
];

const HISTORIAL_RECIENTES = 10;

@Component({
  selector: 'app-panel-disponibilidad',
  standalone: true,
  imports: [
    FormsModule,
    TablerIconComponent,
    DatePipe,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
  ],
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
  readonly historialReciente = computed(() => this.historial().slice(0, HISTORIAL_RECIENTES));

  /** Salidas de la unidad — a qué acudió, no solo cuándo estuvo disponible. */
  readonly despachos = signal<HistorialDespachoUnidadItem[]>([]);
  readonly despachosLoading = signal(false);
  readonly despachosError = signal<string | null>(null);

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
        this.cargarDespachos(res.data.idunidademergencia);
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
    this.disponibilidadApi.consultarHistorial(idunidademergencia, { limit: HISTORIAL_RECIENTES }).subscribe({
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

  cargarDespachos(idunidademergencia: number): void {
    this.despachosLoading.set(true);
    this.despachosError.set(null);
    this.disponibilidadApi
      .listarHistorialDespachos(idunidademergencia, { limit: HISTORIAL_RECIENTES })
      .subscribe({
        next: (res) => {
          this.despachos.set(res.data.items);
          this.despachosLoading.set(false);
        },
        error: () => {
          // Que falle este listado no puede tumbar el panel: declarar la
          // disponibilidad es la función crítica de esta pantalla.
          this.despachosError.set('No se pudo cargar el historial de despachos.');
          this.despachosLoading.set(false);
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
