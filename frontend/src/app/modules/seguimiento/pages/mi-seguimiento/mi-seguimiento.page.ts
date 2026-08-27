import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { EscalarSeveridadPanel } from '../../../accidentes/pages/detalle-accidente/escalar-severidad.panel';
import { ConfirmDialogService } from '../../../../shared/notifications/confirm-dialog.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { MiSeguimientoApiService } from '../../services/mi-seguimiento-api.service';
import { DespachoActualData } from '../../models/seguimiento.types';

type EstadoMision = 'en_camino' | 'en_sitio' | 'abortada';

const INTERVALO_ENVIO_GPS_MS = 10_000;

@Component({
  selector: 'app-mi-seguimiento',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    EscalarSeveridadPanel,
    TablerIconComponent,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './mi-seguimiento.page.html',
})
export class MiSeguimientoPage implements OnInit, OnDestroy {
  private readonly router = inject(Router);
  private readonly api = inject(MiSeguimientoApiService);
  private readonly notifications = inject(NotificationService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  readonly cargando = signal(true);
  readonly despacho = signal<DespachoActualData | null>(null);
  readonly estado = signal<EstadoMision>('en_camino');
  readonly gpsError = signal<string | null>(null);
  readonly apiError = signal<string | null>(null);
  readonly registrandoLlegada = signal(false);
  readonly finalizando = signal(false);
  readonly abortando = signal(false);
  readonly confirmandoAbortar = signal(false);
  readonly modalEscalarAbierto = signal(false);
  motivoAbortar = '';

  private watchId: number | null = null;
  private ultimoEnvioMs = 0;

  abrirModalEscalar(): void {
    this.modalEscalarAbierto.set(true);
  }

  cerrarModalEscalar(): void {
    this.modalEscalarAbierto.set(false);
  }

  onEscalado(): void {
    this.cerrarModalEscalar();
    this.cargarActual();
  }

  ngOnInit(): void {
    this.cargarActual();
  }

  ngOnDestroy(): void {
    this.detenerRastreoGps();
  }

  cargarActual(): void {
    this.cargando.set(true);
    this.apiError.set(null);
    this.api.obtenerActual().subscribe({
      next: (res) => {
        this.cargando.set(false);
        this.despacho.set(res.data.despacho);
        if (res.data.despacho) {
          this.estado.set(res.data.despacho.estado_despacho === 'En_sitio' ? 'en_sitio' : 'en_camino');
          if (res.data.despacho.estado_despacho === 'Confirmado') {
            this.iniciarRastreoGps();
          }
        }
      },
      error: () => {
        this.cargando.set(false);
        this.apiError.set('No se pudo consultar tu despacho activo.');
      },
    });
  }

  private iniciarRastreoGps(): void {
    if (!('geolocation' in navigator)) {
      this.gpsError.set('Este dispositivo no soporta geolocalización.');
      return;
    }
    this.gpsError.set(null);
    this.watchId = navigator.geolocation.watchPosition(
      (position) => this.onPosicion(position),
      () => this.gpsError.set('No se pudo obtener tu ubicación. Revisa los permisos de GPS.'),
      { enableHighAccuracy: true },
    );
  }

  private detenerRastreoGps(): void {
    if (this.watchId !== null) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
  }

  reintentarGps(): void {
    this.iniciarRastreoGps();
  }

  private onPosicion(position: GeolocationPosition): void {
    const despacho = this.despacho();
    if (!despacho) {
      return;
    }
    const ahora = Date.now();
    if (ahora - this.ultimoEnvioMs < INTERVALO_ENVIO_GPS_MS) {
      return;
    }
    this.ultimoEnvioMs = ahora;
    this.api
      .registrarPosicion(
        {
          idunidademergencia: despacho.idunidademergencia,
          idaccidente: despacho.idaccidente,
          latitud: position.coords.latitude,
          longitud: position.coords.longitude,
          fechahora: ahora,
        },
        crypto.randomUUID(),
      )
      .subscribe({
        error: () => this.apiError.set('No se pudo enviar la posición GPS.'),
      });
  }

  registrarLlegada(): void {
    const despacho = this.despacho();
    if (!despacho) {
      return;
    }
    this.registrandoLlegada.set(true);
    this.apiError.set(null);
    this.api.registrarLlegada(despacho.iddespacho, crypto.randomUUID()).subscribe({
      next: () => {
        this.registrandoLlegada.set(false);
        this.estado.set('en_sitio');
        this.detenerRastreoGps();
        this.notifications.toast('Llegada registrada.', 'success');
      },
      error: () => {
        this.registrandoLlegada.set(false);
        this.apiError.set('No se pudo registrar la llegada.');
      },
    });
  }

  /**
   * SRS §3.6.4: la unidad termina su parte. Es la vía normal por la que un
   * despacho queda retirado; el caso solo cierra cuando lo han hecho todas.
   */
  async finalizarAtencion(): Promise<void> {
    const despacho = this.despacho();
    if (!despacho || this.finalizando()) {
      return;
    }
    const confirmado = await this.confirmDialog.confirm({
      title: 'Finalizar mi atención',
      message:
        '¿Das por terminada tu parte de este caso? Tu unidad volverá a estar disponible.',
      confirmLabel: 'Finalizar',
      cancelLabel: 'Seguir en el caso',
    });
    if (!confirmado) {
      return;
    }
    this.finalizando.set(true);
    this.apiError.set(null);
    this.api.finalizarAtencion(despacho.iddespacho, crypto.randomUUID()).subscribe({
      next: (res) => {
        this.finalizando.set(false);
        this.detenerRastreoGps();
        this.notifications.toast(
          res.data.caso_listo_para_cierre
            ? 'Atención finalizada. No quedan unidades en el caso.'
            : `Atención finalizada. Quedan ${res.data.unidades_sin_retirar} unidad(es) en el caso.`,
          'success',
        );
        this.router.navigate(['/despacho/mi-despacho']);
      },
      error: () => {
        this.finalizando.set(false);
        this.apiError.set('No se pudo finalizar la atención.');
      },
    });
  }

  iniciarAbortar(): void {
    this.motivoAbortar = '';
    this.confirmandoAbortar.set(true);
  }

  cancelarAbortar(): void {
    this.confirmandoAbortar.set(false);
    this.motivoAbortar = '';
  }

  confirmarAbortar(): void {
    const despacho = this.despacho();
    if (!despacho) {
      return;
    }
    this.abortando.set(true);
    this.apiError.set(null);
    this.api
      .abortarMision(
        despacho.iddespacho,
        { motivo: this.motivoAbortar || undefined },
        crypto.randomUUID(),
      )
      .subscribe({
        next: () => {
          this.abortando.set(false);
          this.confirmandoAbortar.set(false);
          this.estado.set('abortada');
          this.detenerRastreoGps();
          this.notifications.toast('Misión abortada.', 'success');
          this.router.navigate(['/despacho/mi-despacho']);
        },
        error: () => {
          this.abortando.set(false);
          this.apiError.set('No se pudo abortar la misión.');
        },
      });
  }
}
