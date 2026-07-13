import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

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
  template: `
    <div class="mx-auto max-w-4xl p-8">
      <div class="mb-6 flex items-center justify-between">
        <h1 class="m-0 text-2xl font-bold text-text-primary">Mi despacho</h1>
        @if (!loading() && !error() && pendientes().length) {
          <span class="rounded-md bg-bg-page px-2.5 py-1 text-xs font-medium text-text-secondary">
            {{ pendientes().length }} pendiente(s)
          </span>
        }
      </div>

      @if (loading()) {
        <div class="grid gap-2" data-testid="loading-skeleton">
          @for (i of [1, 2, 3]; track i) {
            <div class="h-24 animate-pulse rounded-lg bg-bg-surface"></div>
          }
        </div>
      } @else if (error()) {
        <div
          class="grid place-items-center gap-3 rounded-lg border border-alert-critical bg-alert-critical-bg p-10 text-center"
          data-testid="error-state"
        >
          <app-tabler-icon name="alert-triangle" [size]="32" />
          <p class="m-0 text-sm text-alert-critical">{{ error() }}</p>
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-md border border-alert-critical px-4 py-2 text-sm font-medium text-alert-critical hover:bg-alert-critical-bg"
            (click)="cargar()"
          >
            <app-tabler-icon name="refresh" [size]="16" />
            Reintentar
          </button>
        </div>
      } @else if (!pendientes().length) {
        <div
          class="grid place-items-center gap-3 rounded-lg border border-border-default bg-bg-surface p-10 text-center"
          data-testid="empty-state"
        >
          <app-tabler-icon name="bell" [size]="32" />
          <p class="m-0 text-sm text-text-secondary">Sin despachos pendientes</p>
        </div>
      } @else {
        <div class="grid gap-4">
          @for (p of pendientes(); track p.idnotificaciondespacho) {
            <article class="rounded-lg border border-border-default bg-bg-surface p-6">
              <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
                <div class="flex items-center gap-3">
                  <h2 class="m-0 text-base font-semibold text-text-primary">{{ p.idaccidente }}</h2>
                  <span
                    class="inline-flex items-center gap-1.5 text-sm font-medium"
                    [class.text-alert-success]="severidad(p.idseveridad).tone === 'success'"
                    [class.text-alert-warning]="severidad(p.idseveridad).tone === 'warning'"
                    [class.text-alert-urgent]="severidad(p.idseveridad).tone === 'urgent'"
                    [class.text-alert-critical]="severidad(p.idseveridad).tone === 'critical'"
                  >
                    <app-tabler-icon [name]="severidad(p.idseveridad).icon" [size]="16" />
                    {{ severidad(p.idseveridad).label }}
                  </span>
                </div>
                <span
                  class="inline-flex items-center rounded-md px-2.5 py-1 text-xs font-semibold"
                  [class.bg-alert-success-bg]="estadoTono(p.estadonotificacion) === 'success'"
                  [class.text-alert-success]="estadoTono(p.estadonotificacion) === 'success'"
                  [class.bg-alert-warning-bg]="estadoTono(p.estadonotificacion) === 'warning'"
                  [class.text-alert-warning]="estadoTono(p.estadonotificacion) === 'warning'"
                  [class.bg-alert-critical-bg]="estadoTono(p.estadonotificacion) === 'critical'"
                  [class.text-alert-critical]="estadoTono(p.estadonotificacion) === 'critical'"
                  [class.bg-alert-info-bg]="estadoTono(p.estadonotificacion) === 'info'"
                  [class.text-alert-info]="estadoTono(p.estadonotificacion) === 'info'"
                >
                  {{ p.estadonotificacion }}
                </span>
              </div>

              <dl class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                @if (p.descripcion) {
                  <div class="sm:col-span-2">
                    <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Descripción</dt>
                    <dd class="mt-1 text-sm text-text-primary">{{ p.descripcion }}</dd>
                  </div>
                }
                @if (p.direccion_aproximada) {
                  <div>
                    <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">Dirección aproximada</dt>
                    <dd class="mt-1 text-sm text-text-primary">{{ p.direccion_aproximada }}</dd>
                  </div>
                }
                @if (p.eta_minutos !== undefined && p.eta_minutos !== null) {
                  <div>
                    <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">ETA</dt>
                    <dd class="mt-1 text-sm text-text-primary">{{ p.eta_minutos }} min</dd>
                  </div>
                }
              </dl>

              @if (rechazandoId() !== p.idnotificaciondespacho) {
                <div class="mt-4 flex gap-2">
                  <button
                    type="button"
                    [disabled]="enviandoId() === p.idnotificaciondespacho"
                    class="inline-flex h-11 items-center gap-2 rounded-md bg-accent-primary px-5 text-sm font-semibold text-white disabled:opacity-50 [&:hover:not(:disabled)]:bg-accent-hover"
                    (click)="confirmar(p.idnotificaciondespacho)"
                  >
                    <app-tabler-icon name="circle-check" [size]="18" />
                    Confirmar
                  </button>
                  <button
                    type="button"
                    [disabled]="enviandoId() === p.idnotificaciondespacho"
                    class="inline-flex h-11 items-center gap-2 rounded-md border border-alert-warning px-5 text-sm font-medium text-alert-warning disabled:opacity-50 hover:bg-alert-warning-bg"
                    (click)="iniciarRechazo(p.idnotificaciondespacho)"
                  >
                    <app-tabler-icon name="x" [size]="18" />
                    Rechazar
                  </button>
                </div>
              } @else {
                <div class="mt-4 grid gap-3 rounded-lg border border-alert-warning bg-alert-warning-bg p-4">
                  <label for="motivoRechazo-{{ p.idnotificaciondespacho }}" class="text-sm font-medium text-text-secondary">
                    Motivo del rechazo (obligatorio)
                  </label>
                  <textarea
                    id="motivoRechazo-{{ p.idnotificaciondespacho }}"
                    rows="2"
                    required
                    class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
                    [(ngModel)]="motivoRechazo"
                    name="motivoRechazo-{{ p.idnotificaciondespacho }}"
                  ></textarea>
                  <div class="flex gap-2">
                    <button
                      type="button"
                      [disabled]="!motivoRechazo.trim() || enviandoId() === p.idnotificaciondespacho"
                      class="inline-flex h-11 items-center gap-2 rounded-md bg-alert-warning px-5 text-sm font-semibold text-white disabled:opacity-50"
                      (click)="confirmarRechazo(p.idnotificaciondespacho)"
                    >
                      Confirmar rechazo
                    </button>
                    <button
                      type="button"
                      [disabled]="enviandoId() === p.idnotificaciondespacho"
                      class="inline-flex h-11 items-center gap-2 rounded-md border border-border-default px-5 text-sm font-medium text-text-primary hover:bg-bg-page"
                      (click)="cancelarRechazo()"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              }
            </article>
          }
        </div>
      }
    </div>
  `,
})
export class MiDespachoPage implements OnInit {
  private readonly api = inject(MiDespachoApiService);
  private readonly notifications = inject(NotificationService);

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
        this.cargar();
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
