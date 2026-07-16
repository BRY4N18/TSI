import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { catchError, of, timeout } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ReadOnlyRouteMapComponent } from '../../../../shared/ui/map/read-only-route-map.component';
import { SEVERIDAD_INFO, SeveridadInfo } from '../../../accidentes/severidad.constants';
import { estadoNotificacionTono } from '../../despacho-tono.constants';
import { MiDespachoApiService } from '../../services/mi-despacho-api.service';
import { PendienteDespacho } from '../../services/models/despacho.types';

/**
 * `GET /despacho/parametros` (donde vive el valor real de timeout_respuesta_seg)
 * requiere rol Director Tecnológico/Administrador — el rol Unidad no puede leerlo.
 * Se usa el mismo default documentado en
 * `core/repositories/despacho/parametros_despacho_repository.py` (90s) para el
 * countdown visual. Si se necesita el valor exacto configurado, habría que
 * exponerlo en el propio payload de `/mi-despacho/*` (fuera de alcance de este
 * cambio).
 */
const TIMEOUT_RESPUESTA_DEFAULT_SEG = 90;
const RESPUESTA_TIMEOUT_MS = 15_000; // design-system.md §5: máx 10-15s antes de revertir el estado "en carga"

@Component({
  selector: 'app-mi-despacho',
  standalone: true,
  imports: [FormsModule, TablerIconComponent, ReadOnlyRouteMapComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './mi-despacho.page.html',
})
export class MiDespachoPage implements OnInit {
  private readonly api = inject(MiDespachoApiService);
  private readonly notifications = inject(NotificationService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly pendientes = signal<PendienteDespacho[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly rechazandoId = signal<number | null>(null);
  readonly enviandoId = signal<number | null>(null);
  motivoRechazo = '';

  readonly estadoTono = estadoNotificacionTono;

  /** El incidente más urgente ocupa el dashboard completo; el resto queda en cola. */
  readonly incidenteActivo = computed<PendienteDespacho | null>(() => this.pendientes()[0] ?? null);
  readonly colaPendientes = computed<PendienteDespacho[]>(() => this.pendientes().slice(1));

  private readonly restanteMsInterno = signal<number | null>(null);
  readonly restanteMs = this.restanteMsInterno.asReadonly();
  readonly restanteLabel = computed(() => {
    const ms = this.restanteMsInterno();
    if (ms === null) {
      return null;
    }
    const totalSeg = Math.max(0, Math.round(ms / 1000));
    const min = Math.floor(totalSeg / 60);
    const seg = totalSeg % 60;
    return `${min.toString().padStart(2, '0')}:${seg.toString().padStart(2, '0')}`;
  });

  private countdownIntervalId: ReturnType<typeof setInterval> | null = null;
  private countdownIncidenteId: number | null = null;

  ngOnInit(): void {
    this.cargar();
    this.destroyRef.onDestroy(() => this.detenerCountdown());
  }

  severidad(idseveridad: number): SeveridadInfo {
    return (
      SEVERIDAD_INFO[idseveridad] ?? {
        value: idseveridad,
        label: `Sev. ${idseveridad}`,
        icon: 'info-circle',
        tone: 'success',
      }
    );
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listarPendientes().subscribe({
      next: (res) => {
        this.pendientes.set(res.data.pendientes);
        this.loading.set(false);
        this.sincronizarCountdown();
      },
      error: () => {
        this.error.set('No se pudo cargar la lista de despachos pendientes.');
        this.loading.set(false);
      },
    });
  }

  /** Promueve un pendiente de la cola compacta al frente del dashboard. */
  promoverAlFrente(id: number): void {
    const actual = this.pendientes();
    const idx = actual.findIndex((p) => p.idnotificaciondespacho === id);
    if (idx <= 0) {
      return;
    }
    const reordenado = [actual[idx], ...actual.slice(0, idx), ...actual.slice(idx + 1)];
    this.pendientes.set(reordenado);
    this.sincronizarCountdown();
  }

  confirmar(id: number): void {
    this.enviandoId.set(id);
    this.api
      .confirmar(id)
      .pipe(
        timeout(RESPUESTA_TIMEOUT_MS),
        catchError(() => of(null)),
      )
      .subscribe((res) => {
        this.enviandoId.set(null);
        if (!res) {
          this.notifications.alert('No se pudo confirmar el despacho.', 'Error al confirmar');
          return;
        }
        this.notifications.toast(res.data.message, 'success');
        this.router.navigate(['/seguimiento/mi-seguimiento']);
      });
  }

  iniciarRechazo(id: number): void {
    this.motivoRechazo = '';
    this.rechazandoId.set(id);
  }

  cancelarRechazo(): void {
    this.rechazandoId.set(null);
    this.motivoRechazo = '';
  }

  confirmarRechazo(id: number): void {
    if (!this.motivoRechazo.trim()) {
      return;
    }
    this.enviandoId.set(id);
    this.api
      .rechazar(id, { motivo: this.motivoRechazo })
      .pipe(
        timeout(RESPUESTA_TIMEOUT_MS),
        catchError(() => of(null)),
      )
      .subscribe((res) => {
        this.enviandoId.set(null);
        if (!res) {
          this.notifications.alert('No se pudo rechazar el despacho.', 'Error al rechazar');
          return;
        }
        this.rechazandoId.set(null);
        this.motivoRechazo = '';
        this.notifications.toast(res.data.message, 'success');
        this.cargar();
      });
  }

  private sincronizarCountdown(): void {
    const incidente = this.incidenteActivo();
    if (!incidente || typeof incidente.fechahora !== 'number' || Number.isNaN(incidente.fechahora)) {
      this.detenerCountdown();
      return;
    }
    if (this.countdownIncidenteId === incidente.idnotificaciondespacho) {
      return; // ya corriendo para este incidente, no reiniciar el countdown
    }
    this.detenerCountdown();
    this.countdownIncidenteId = incidente.idnotificaciondespacho;
    const deadlineMs = incidente.fechahora + TIMEOUT_RESPUESTA_DEFAULT_SEG * 1000;
    const tick = () => this.restanteMsInterno.set(deadlineMs - Date.now());
    tick();
    this.countdownIntervalId = setInterval(tick, 1000);
  }

  private detenerCountdown(): void {
    if (this.countdownIntervalId !== null) {
      clearInterval(this.countdownIntervalId);
      this.countdownIntervalId = null;
    }
    this.countdownIncidenteId = null;
    this.restanteMsInterno.set(null);
  }
}
