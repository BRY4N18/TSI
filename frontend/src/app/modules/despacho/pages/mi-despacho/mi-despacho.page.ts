import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { SEVERIDAD_INFO, SeveridadInfo } from '../../../accidentes/severidad.constants';
import { estadoNotificacionTono } from '../../despacho-tono.constants';
import { MiDespachoApiService } from '../../services/mi-despacho-api.service';
import { PendienteDespacho } from '../../services/models/despacho.types';

@Component({
  selector: 'app-mi-despacho',
  standalone: true,
  imports: [FormsModule, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './mi-despacho.page.html',
})
export class MiDespachoPage implements OnInit {
  private readonly api = inject(MiDespachoApiService);
  private readonly notifications = inject(NotificationService);
  private readonly router = inject(Router);

  readonly pendientes = signal<PendienteDespacho[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly rechazandoId = signal<number | null>(null);
  readonly enviandoId = signal<number | null>(null);
  motivoRechazo = '';

  readonly estadoTono = estadoNotificacionTono;

  ngOnInit(): void {
    this.cargar();
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
      },
      error: () => {
        this.error.set('No se pudo cargar la lista de despachos pendientes.');
        this.loading.set(false);
      },
    });
  }

  confirmar(id: number): void {
    this.enviandoId.set(id);
    this.api.confirmar(id).subscribe({
      next: (res) => {
        this.enviandoId.set(null);
        this.notifications.toast(res.data.message, 'success');
        this.router.navigate(['/seguimiento/mi-seguimiento']);
      },
      error: () => {
        this.enviandoId.set(null);
        this.notifications.alert('No se pudo confirmar el despacho.', 'Error al confirmar');
      },
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
    this.api.rechazar(id, { motivo: this.motivoRechazo }).subscribe({
      next: (res) => {
        this.enviandoId.set(null);
        this.rechazandoId.set(null);
        this.motivoRechazo = '';
        this.notifications.toast(res.data.message, 'success');
        this.cargar();
      },
      error: () => {
        this.enviandoId.set(null);
        this.notifications.alert('No se pudo rechazar el despacho.', 'Error al rechazar');
      },
    });
  }
}
