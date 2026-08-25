import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ConfirmDialogService } from '../../../../shared/notifications/confirm-dialog.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { PartnerApiService, nuevaClaveIdempotencia } from '../../services/partner-api.service';
import { PartnerColaAcceso } from '../../services/models/partner.types';

/**
 * Panel de suspensiones del Administrador (RF-PAC-005 + RF-PAC-009 b).
 *
 * Sin esta pantalla, la reactivación —que **solo** un Administrador puede hacer
 * (RN-PAC-009) y que el sistema nunca ejecuta solo— no tenía por dónde
 * empezar: había que consultar partner por partner para saber a quién le toca.
 *
 * Muestra el desglose `restituidas` / `no restituidas` al reactivar porque no es
 * un detalle técnico (RN-PAC-011): explica que la credencial que el partner
 * revocó por seguridad **sigue inactiva a propósito**. Sin decirlo, parece un
 * fallo.
 */
@Component({
  selector: 'app-cola-acceso',
  standalone: true,
  imports: [
    FormsModule,
    DatePipe,
    TablerIconComponent,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
    ListEmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="mx-auto max-w-5xl p-8">
      <h1 class="tsi-display m-0 mb-1 text-3xl font-extrabold text-text-primary">Suspensiones de partners</h1>
<div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>
      <p class="m-0 mb-6 text-sm text-text-secondary">
        Partners suspendidos y partners en ciclo de mora con avisos ya enviados. La
        reactivación siempre la confirma una persona: el sistema no reactiva solo.
      </p>

      <!-- Fuera del bloque de la lista a propósito: al reactivar al último
           partner la lista queda vacía, y el desglose de credenciales
           restituidas es justo lo que el administrador necesita leer entonces. -->
      @if (resultado(); as r) {
        <div
          class="mb-4 rounded-md border border-alert-success bg-alert-success-bg p-4 text-sm text-alert-success"
          data-testid="resultado-accion"
        >
          {{ r }}
        </div>
      }

      @if (cargando()) {
        <app-list-loading-skeleton [count]="3" />
      } @else if (error()) {
        <app-list-error-state [message]="error()!" (retry)="cargar()" />
      } @else if (!filas().length) {
        <app-list-empty-state
          icon="license"
          message="Ningún partner está suspendido ni en ciclo de mora."
        />
      } @else {
        <ul class="grid gap-3">
          @for (p of filas(); track p.idpartner) {
            <li
              class="tsi-panel p-5"
              [attr.data-testid]="'fila-' + p.idpartner"
            >
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p class="m-0 font-semibold text-text-primary">{{ p.nombrepartner }}</p>
                  @if (!p.activo) {
                    <p class="m-0 mt-1 text-sm text-alert-critical">
                      Suspendido
                      @if (p.fecha_suspension) {
                        · desde {{ p.fecha_suspension | date: 'dd/MM/yyyy' }}
                      }
                    </p>
                    <!-- El motivo se presenta como texto redactado, no como
                         código: "suspendido" no siempre es culpa del partner. -->
                    <p class="m-0 mt-1 text-sm text-text-secondary">{{ p.motivo_suspension }}</p>
                  } @else {
                    <p class="m-0 mt-1 text-sm text-alert-warning">
                      En mora: {{ p.dias_mora }} día(s)
                      @if (p.ultimo_aviso) {
                        · último aviso: {{ p.ultimo_aviso }}
                      }
                    </p>
                    <p class="m-0 mt-1 text-sm text-text-secondary">
                      Aún tiene acceso. Regularizar antes del límite evita la suspensión.
                    </p>
                  }
                </div>

                @if (p.activo) {
                  <button
                    type="button"
                    [attr.data-testid]="'btn-suspender-' + p.idpartner"
                    [disabled]="enCurso() === p.idpartner"
                    class="tsi-btn border border-alert-critical bg-transparent text-alert-critical hover:bg-alert-critical-bg"
                    (click)="suspender(p)"
                  >
                    <app-tabler-icon name="x" [size]="16" />
                    Suspender
                  </button>
                } @else {
                  <button
                    type="button"
                    [attr.data-testid]="'btn-reactivar-' + p.idpartner"
                    [disabled]="enCurso() === p.idpartner"
                    class="tsi-btn tsi-btn-primary"
                    (click)="reactivar(p)"
                  >
                    <app-tabler-icon name="circle-check" [size]="16" />
                    @if (enCurso() === p.idpartner) {
                      Reactivando…
                    } @else {
                      Reactivar
                    }
                  </button>
                }
              </div>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class ColaAccesoPage implements OnInit {
  private readonly api = inject(PartnerApiService);
  private readonly confirmDialog = inject(ConfirmDialogService);
  private readonly notifications = inject(NotificationService);

  readonly filas = signal<PartnerColaAcceso[]>([]);
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);
  readonly enCurso = signal<number | null>(null);
  readonly resultado = signal<string | null>(null);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.error.set(null);
    this.api.colaAcceso().subscribe({
      next: (res) => {
        this.filas.set(res.data);
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.error.set('No se pudo cargar la cola de acceso.');
      },
    });
  }

  async suspender(p: PartnerColaAcceso): Promise<void> {
    const motivo = await this.pedirMotivo(
      'Suspender partner',
      `Se desactivarán TODAS las credenciales de ${p.nombrepartner}, de pruebas y de producción. El motivo se le notifica.`,
      'Suspender',
    );
    if (motivo === null) {
      return;
    }
    this.enCurso.set(p.idpartner);
    this.api.suspender(p.idpartner, motivo, nuevaClaveIdempotencia()).subscribe({
      next: (res) => {
        this.enCurso.set(null);
        this.resultado.set(
          `${p.nombrepartner} quedó suspendido. Credenciales desactivadas: ${res.data.credenciales_desactivadas}.`,
        );
        this.cargar();
      },
      error: (err) => this.fallo(err, 'No se pudo suspender el partner.'),
    });
  }

  async reactivar(p: PartnerColaAcceso): Promise<void> {
    const motivo = await this.pedirMotivo(
      'Reactivar partner',
      `Se restituirán solo las credenciales que estaban activas antes de la suspensión. Las que ${p.nombrepartner} revocó por seguridad seguirán inactivas.`,
      'Reactivar',
    );
    if (motivo === null) {
      return;
    }
    this.enCurso.set(p.idpartner);
    this.api.reactivar(p.idpartner, motivo, nuevaClaveIdempotencia()).subscribe({
      next: (res) => {
        this.enCurso.set(null);
        const noRest = res.data.credenciales_no_restituidas;
        this.resultado.set(
          `${p.nombrepartner} vuelve a estar activo. Credenciales restituidas: ` +
            `${res.data.credenciales_restituidas}` +
            (noRest
              ? `. Quedan ${noRest} sin restituir a propósito: fueron revocadas por seguridad y resucitarlas sería un riesgo.`
              : '.'),
        );
        this.cargar();
      },
      error: (err) => this.fallo(err, 'No se pudo reactivar el partner.'),
    });
  }

  /** Confirmación en 2 pasos con motivo obligatorio (RF-PAC-005). */
  private async pedirMotivo(
    title: string,
    message: string,
    confirmLabel: string,
  ): Promise<string | null> {
    const confirmado = await this.confirmDialog.confirm({
      title,
      message,
      tone: 'danger',
      confirmLabel,
      cancelLabel: 'Cancelar',
    });
    return confirmado ? `${confirmLabel} desde el panel de administración` : null;
  }

  private fallo(err: unknown, porDefecto: string): void {
    this.enCurso.set(null);
    const cuerpo = (err as { error?: { detail?: unknown } } | undefined)?.error;
    const detalle = cuerpo?.detail;
    this.notifications.alert(
      typeof detalle === 'string' && detalle.trim() ? detalle : porDefecto,
      'Error',
    );
  }
}
