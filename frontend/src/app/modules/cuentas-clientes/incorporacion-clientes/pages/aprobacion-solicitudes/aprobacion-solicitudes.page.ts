import { ChangeDetectorRef, Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { NotificationService } from '../../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { IncorporacionClienteApiService } from '../../services/incorporacion-cliente-api.service';
import { SolicitudItem } from '../../models/incorporacion-cliente.contract';

@Component({
  selector: 'app-aprobacion-solicitudes-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TablerIconComponent],
  templateUrl: './aprobacion-solicitudes.page.html',
})
export class AprobacionSolicitudesPage implements OnInit {
  private readonly api = inject(IncorporacionClienteApiService);
  private readonly notifications = inject(NotificationService);
  // El shell de la aplicación es OnPush: sin marcar la vista, nada de lo que
  // llega por HTTP se repinta. Ver §9 del design-system.
  private readonly cdr = inject(ChangeDetectorRef);

  pendientes: SolicitudItem[] = [];
  rechazadas: SolicitudItem[] = [];
  cargando = false;
  procesando = false;

  rechazoTarget: SolicitudItem | null = null;
  motivoRechazo = '';
  motivoError = false;

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.api.listarSolicitudes('Pendiente_Aprobación').subscribe({
      next: (res) => {
        this.cdr.markForCheck();
        this.pendientes = res.data ?? [];
        this.api.listarSolicitudes('Rechazado').subscribe({
          next: (rej) => {
        this.cdr.markForCheck();
            this.cargando = false;
            this.rechazadas = rej.data ?? [];
          },
          error: (err) => {
        this.cdr.markForCheck();
            this.cargando = false;
            this.notifications.toast(
              err?.error?.detail || 'No se pudieron cargar rechazadas',
              'critical',
            );
          },
        });
      },
      error: (err) => {
        this.cdr.markForCheck();
        this.cargando = false;
        this.notifications.toast(
          err?.error?.detail || 'No se pudieron cargar solicitudes',
          'critical',
        );
      },
    });
  }

  aprobar(s: SolicitudItem): void {
    this.procesando = true;
    this.api.decidirSolicitud(s.idcliente, { decision: 'aprobar' }).subscribe({
      next: () => {
        this.cdr.markForCheck();
        this.procesando = false;
        this.notifications.toast(
          `Solicitud #${s.idcliente} aprobada. Se envió notificación.`,
          'success',
        );
        this.cargar();
      },
      error: (err) => {
        this.cdr.markForCheck();
        this.procesando = false;
        this.notifications.toast(err?.error?.detail || 'No se pudo aprobar', 'critical');
      },
    });
  }

  abrirRechazo(s: SolicitudItem): void {
    this.rechazoTarget = s;
    this.motivoRechazo = '';
    this.motivoError = false;
  }

  cerrarRechazo(): void {
    this.rechazoTarget = null;
    this.motivoRechazo = '';
    this.motivoError = false;
  }

  confirmarRechazo(): void {
    const target = this.rechazoTarget;
    const motivo = this.motivoRechazo.trim();
    if (!target) {
      return;
    }
    if (!motivo) {
      this.motivoError = true;
      return;
    }
    this.motivoError = false;
    this.procesando = true;
    this.api.decidirSolicitud(target.idcliente, { decision: 'rechazar', motivo }).subscribe({
      next: () => {
        this.cdr.markForCheck();
        this.procesando = false;
        this.cerrarRechazo();
        this.notifications.toast(
          `Solicitud #${target.idcliente} rechazada. Se envió notificación.`,
          'warning',
        );
        this.cargar();
      },
      error: (err) => {
        this.cdr.markForCheck();
        this.procesando = false;
        this.notifications.toast(err?.error?.detail || 'No se pudo rechazar', 'critical');
      },
    });
  }

  anular(s: SolicitudItem): void {
    this.procesando = true;
    this.api.anularRechazo(s.idcliente).subscribe({
      next: () => {
        this.cdr.markForCheck();
        this.procesando = false;
        this.notifications.toast(
          `Rechazo #${s.idcliente} anulado. El NIT queda libre.`,
          'success',
        );
        this.cargar();
      },
      error: (err) => {
        this.cdr.markForCheck();
        this.procesando = false;
        this.notifications.toast(err?.error?.detail || 'No se pudo anular', 'critical');
      },
    });
  }

  reenviar(s: SolicitudItem): void {
    this.procesando = true;
    this.api.reenviarInvitacion(s.idcliente).subscribe({
      next: () => {
        this.cdr.markForCheck();
        this.procesando = false;
        this.notifications.toast(`Invitación reenviada para #${s.idcliente}.`, 'info');
      },
      error: (err) => {
        this.cdr.markForCheck();
        this.procesando = false;
        this.notifications.toast(
          err?.error?.detail || 'No se pudo reenviar la invitación',
          'critical',
        );
      },
    });
  }
}
