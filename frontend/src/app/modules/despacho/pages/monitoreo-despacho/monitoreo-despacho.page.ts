import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ConfirmDialogService } from '../../../../shared/notifications/confirm-dialog.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { SeguimientoApiService } from '../../../seguimiento/services/seguimiento-api.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { RouteTrackerComponent, RouteTrackerStep } from '../../../../shared/ui/route-tracker/route-tracker.component';
import { estadoInfo } from '../../../accidentes/estado.constants';
import { estadoDespachoLabel, estadoDespachoTono } from '../../despacho-tono.constants';
import { DespachoApiService } from '../../services/despacho-api.service';
import { DespachoSseService } from '../../services/despacho-sse.service';
import { EstadoDespachoData, IntentoDespacho } from '../../services/models/despacho.types';

type SyncStatus = 'live' | 'reconnecting' | 'offline';

const SYNC_LABEL: Record<SyncStatus, string> = {
  live: 'En vivo',
  reconnecting: 'Conectando…',
  offline: 'Sin conexión en vivo',
};

@Component({
  selector: 'app-monitoreo-despacho',
  standalone: true,
  imports: [
    RouterLink,
    FormsModule,
    DatePipe,
    TablerIconComponent,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    RouteTrackerComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './monitoreo-despacho.page.html',
})
export class MonitoreoDespachoPage implements OnInit {
  private readonly api = inject(DespachoApiService);
  private readonly sse = inject(DespachoSseService);
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  idaccidente = '';
  readonly estado = signal<EstadoDespachoData | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly syncStatus = signal<SyncStatus>('reconnecting');
  readonly tiempoTranscurrido = signal(0);

  readonly estado_ = estadoInfo;
  readonly intentoTono = estadoDespachoTono;
  readonly intentoLabel = estadoDespachoLabel;

  // --- Cierre del caso (SRS §3.6.4) ---
  private readonly seguimiento = inject(SeguimientoApiService);
  private readonly notifications = inject(NotificationService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  readonly cerrando = signal(false);
  readonly cancelando = signal(false);
  readonly forzando = signal<number | null>(null);
  readonly cierreError = signal<string | null>(null);
  resultadoAtencion = '';
  observacionesFinales = '';

  /** Estados en los que el caso está vivo y puede cerrarse o cancelarse. */
  puedeCerrarse(estadoCaso: string): boolean {
    return ['ASIGNADO', 'EN_ATENCIÓN', 'BUSCANDO_UNIDAD', 'REPORTADO'].includes(estadoCaso);
  }

  /** Solo tiene sentido forzar el retiro de quien sigue en el caso. */
  esRetirable(estadoDespacho: string): boolean {
    return ['Confirmado', 'En_sitio', 'En_transito'].includes(estadoDespacho);
  }

  async forzarRetiro(iddespacho: number, unidad: string): Promise<void> {
    const confirmado = await this.confirmDialog.confirm({
      title: 'Forzar retiro',
      message: `Vas a retirar a ${unidad} desde central. Quedará registrado como retiro forzado, no como una finalización normal.`,
      tone: 'danger',
      confirmLabel: 'Forzar retiro',
      cancelLabel: 'Cancelar',
    });
    if (!confirmado) {
      return;
    }
    this.forzando.set(iddespacho);
    this.cierreError.set(null);
    this.seguimiento.forzarRetiro(iddespacho).subscribe({
      next: (res) => {
        this.forzando.set(null);
        this.notifications.toast(
          res.data.caso_cerrado
            ? 'Unidad retirada. Con ella se completó el caso, que queda cerrado.'
            : 'Unidad retirada. El caso sigue abierto con el resto de unidades.',
          'success',
        );
        this.cargar();
      },
      error: (err) => {
        this.forzando.set(null);
        this.cierreError.set(this.detalle(err) ?? 'No se pudo forzar el retiro.');
      },
    });
  }

  async cerrarCaso(): Promise<void> {
    if (!this.resultadoAtencion.trim()) {
      this.cierreError.set('Indica el resultado de la atención para cerrar el caso.');
      return;
    }
    const confirmado = await this.confirmDialog.confirm({
      title: 'Cerrar caso',
      message: '¿Cerrar el caso? Se registrará la hora de finalización y su duración total.',
      confirmLabel: 'Cerrar caso',
      cancelLabel: 'Volver',
    });
    if (!confirmado) {
      return;
    }
    this.cerrando.set(true);
    this.cierreError.set(null);
    this.seguimiento
      .cerrarCaso(this.idaccidente, {
        resultado_atencion: this.resultadoAtencion.trim(),
        observaciones_finales: this.observacionesFinales.trim() || undefined,
      })
      .subscribe({
        next: (res) => {
          this.cerrando.set(false);
          this.notifications.toast(
            `Caso cerrado. Duración total: ${res.data.duracionminutos} min.`,
            'success',
          );
          this.cargar();
        },
        error: (err) => {
          this.cerrando.set(false);
          this.cierreError.set(this.detalle(err) ?? 'No se pudo cerrar el caso.');
        },
      });
  }

  async cancelarCaso(): Promise<void> {
    const confirmado = await this.confirmDialog.confirm({
      title: 'Cancelar caso',
      message:
        'Se retirarán las unidades despachadas y el caso se cerrará por vía corta, como falsa alarma detectada tarde.',
      tone: 'danger',
      confirmLabel: 'Cancelar caso',
      cancelLabel: 'Volver',
    });
    if (!confirmado) {
      return;
    }
    this.cancelando.set(true);
    this.cierreError.set(null);
    this.seguimiento
      .cancelarCaso(this.idaccidente, { motivo: 'Falsa alarma detectada tras el despacho' })
      .subscribe({
        next: () => {
          this.cancelando.set(false);
          this.notifications.toast('Caso cancelado y unidades liberadas.', 'success');
          this.cargar();
        },
        error: (err) => {
          this.cancelando.set(false);
          this.cierreError.set(this.detalle(err) ?? 'No se pudo cancelar el caso.');
        },
      });
  }

  /** El backend explica en `detail` por qué no se puede cerrar todavía. */
  private detalle(err: unknown): string | null {
    const cuerpo = (err as { error?: { detail?: unknown } } | undefined)?.error;
    const detalle = cuerpo?.detail;
    return typeof detalle === 'string' && detalle.trim() ? detalle : null;
  }

  ngOnInit(): void {
    this.idaccidente = this.route.snapshot.paramMap.get('idaccidente') ?? '';
    this.cargar();
    this.conectarSse();

    const tick = setInterval(() => this.tiempoTranscurrido.update((v) => v + 1), 1000);
    this.destroyRef.onDestroy(() => clearInterval(tick));
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.obtenerEstado(this.idaccidente).subscribe({
      next: (res) => {
        this.estado.set(res.data);
        this.tiempoTranscurrido.set(res.data.tiempo_transcurrido_seg);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar el estado del despacho.');
        this.loading.set(false);
      },
    });
  }

  private conectarSse(): void {
    // `streamResiliente` reintenta sola y avisa de cada transicion. Antes esto
    // se suscribia al stream crudo: un corte dejaba la pantalla muerta para
    // siempre, y un cierre limpio la dejaba diciendo «En vivo» sobre datos
    // congelados (PG-UI-005).
    this.sse.streamResiliente(this.idaccidente, this.destroyRef).subscribe((update) => {
      this.syncStatus.set(update.estado);
      if (update.evento) {
        this.cargar();
      }
    });
  }

  syncLabel(status: SyncStatus): string {
    return SYNC_LABEL[status];
  }

  ordenados(intentos: IntentoDespacho[]): IntentoDespacho[] {
    return [...intentos].sort((a, b) => b.fechahoradespacho - a.fechahoradespacho);
  }

  /** Historial de intentos como vía de nodos (design-system.md §3.1/v9). */
  pasosIntentos(intentos: IntentoDespacho[]): RouteTrackerStep[] {
    return intentos.map((i) => ({
      title: i.unidademergencia,
      status: i.estado,
      tone: this.intentoTono(i.estado),
      detail: i.motivo ? `${i.origen} — ${i.motivo}` : i.origen,
    }));
  }

  formatTiempo(segundos: number): string {
    const h = Math.floor(segundos / 3600)
      .toString()
      .padStart(2, '0');
    const m = Math.floor((segundos % 3600) / 60)
      .toString()
      .padStart(2, '0');
    const s = Math.floor(segundos % 60)
      .toString()
      .padStart(2, '0');
    return `${h}:${m}:${s}`;
  }
}
