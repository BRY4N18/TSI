import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { MiSeguimientoApiService } from '../../services/mi-seguimiento-api.service';
import { DespachoActualData } from '../../models/seguimiento.types';

type EstadoMision = 'en_camino' | 'en_sitio' | 'abortada';

const INTERVALO_ENVIO_GPS_MS = 10_000;

@Component({
  selector: 'app-mi-seguimiento',
  standalone: true,
  imports: [FormsModule, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './mi-seguimiento.page.html',
})
export class MiSeguimientoPage implements OnInit, OnDestroy {
  private readonly router = inject(Router);
  private readonly api = inject(MiSeguimientoApiService);
  private readonly notifications = inject(NotificationService);

  readonly cargando = signal(true);
  readonly despacho = signal<DespachoActualData | null>(null);
  readonly estado = signal<EstadoMision>('en_camino');
  readonly gpsError = signal<string | null>(null);
  readonly apiError = signal<string | null>(null);
  readonly registrandoLlegada = signal(false);
  readonly abortando = signal(false);
  readonly confirmandoAbortar = signal(false);
  motivoAbortar = '';

  private watchId: number | null = null;
  private ultimoEnvioMs = 0;

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
