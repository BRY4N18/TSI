import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { SolicitudCambioPlan } from '../../services/models/suscripciones.types';
import { SuscripcionApiService } from '../../services/suscripcion-api.service';

@Component({
  selector: 'app-aprobaciones-downgrade',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './aprobaciones-downgrade.page.html',
})
export class AprobacionesDowngradePage implements OnInit {
  private readonly api = inject(SuscripcionApiService);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly pendientes = signal<SolicitudCambioPlan[]>([]);
  readonly message = signal<string | null>(null);
  readonly busyId = signal<number | null>(null);

  motivos: Record<number, string> = {};

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listarSolicitudesCambioPlan({ estado: 'Pendiente', limit: 50 }).subscribe({
      next: (res) => {
        this.pendientes.set(res.data ?? []);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Error al cargar aprobaciones.');
        this.loading.set(false);
      },
    });
  }

  aprobar(s: SolicitudCambioPlan): void {
    if (!s.idsolicitud) return;
    this.busyId.set(s.idsolicitud);
    this.message.set(null);
    this.api.aprobarCambioPlan(s.idsolicitud, crypto.randomUUID()).subscribe({
      next: () => {
        this.message.set(`Solicitud #${s.idsolicitud} aprobada.`);
        this.busyId.set(null);
        this.cargar();
      },
      error: (err) => {
        this.message.set(err?.error?.detail ?? 'No se pudo aprobar.');
        this.busyId.set(null);
      },
    });
  }

  rechazar(s: SolicitudCambioPlan): void {
    if (!s.idsolicitud) return;
    const motivo = (this.motivos[s.idsolicitud] || '').trim();
    if (!motivo) {
      this.message.set('Indica un motivo de rechazo.');
      return;
    }
    this.busyId.set(s.idsolicitud);
    this.message.set(null);
    this.api.rechazarCambioPlan(s.idsolicitud, { motivo_rechazo: motivo }, crypto.randomUUID()).subscribe({
      next: () => {
        this.message.set(`Solicitud #${s.idsolicitud} rechazada.`);
        this.busyId.set(null);
        this.cargar();
      },
      error: (err) => {
        this.message.set(err?.error?.detail ?? 'No se pudo rechazar.');
        this.busyId.set(null);
      },
    });
  }
}
