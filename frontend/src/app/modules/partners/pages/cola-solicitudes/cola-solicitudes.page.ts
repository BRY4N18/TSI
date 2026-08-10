import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListEmptyStateComponent } from '../../../../shared/ui/list-states/list-empty-state.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../shared/ui/list-states/list-table.styles';
import { ESTADO_PENDIENTE_APROBACION } from '../../estado-partner.constants';
import { ROL_RESUELVE_PROMOCION } from '../../guards/administrador-promocion.guard';
import {
  PartnerApiService,
  nuevaClaveIdempotencia,
} from '../../services/partner-api.service';
import type { PartnerListItem } from '../../services/models/partner.types';

const MOTIVO_MINIMO = 15;
const TIMEOUT_ACCION_MS = 15_000;

/**
 * Cola de solicitudes de paso a producción (RF-PON-007 / RF-PON-008).
 *
 * Es una **vista de trabajo**, no un listado más: la aprobación es humana por
 * diseño (SRS L382), así que sin esta pantalla las solicitudes esperarían a que
 * alguien mirara por casualidad. Su estado vacío es un resultado deseable, no
 * un error.
 *
 * Dos decisiones que no son cosméticas:
 *
 * - **Aprobar NO muestra ningún secreto.** El backend devuelve la credencial
 *   productiva, pero mostrarla aquí obligaría al Administrador a transmitir por
 *   correo o chat un secreto ajeno. El partner la emite desde su portal y la ve
 *   él (FR-UI-009, BE-DELTA-02).
 * - **El Desarrollador de APIs ve la cola pero no la resuelve.** Si pudiera, la
 *   aprobación humana dejaría de existir como separación de actores.
 */
@Component({
  selector: 'app-cola-solicitudes',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    TablerIconComponent,
    ListEmptyStateComponent,
    ListErrorStateComponent,
    ListLoadingSkeletonComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <header class="mb-6">
        <h1 class="m-0 text-2xl font-bold text-text-primary">Solicitudes pendientes</h1>
        <p class="mt-1 text-sm text-text-secondary">
          Paso a producción — requiere aprobación de un Administrador
        </p>
      </header>

      @if (avisoConcurrencia()) {
        <div
          class="mb-4 rounded-lg border border-alert-media bg-alert-media-bg p-4 text-sm text-alert-media"
          data-testid="aviso-ya-resuelta"
          role="alert"
        >
          Esta solicitud ya fue resuelta por otro administrador. Se actualizó la lista.
        </div>
      }

      @if (errorAccion()) {
        <div
          class="mb-4 rounded-lg border border-alert-critical bg-alert-critical-bg p-4 text-sm text-alert-critical"
          data-testid="banner-error"
          role="alert"
        >
          {{ errorAccion() }}
        </div>
      }

      @if (confirmacion()) {
        <div
          class="mb-4 rounded-lg border border-exito bg-exito-bg p-4 text-sm text-exito"
          data-testid="banner-confirmacion"
          role="status"
        >
          {{ confirmacion() }}
        </div>
      }

      @if (cargando()) {
        <app-list-loading-skeleton [count]="3" />
      } @else if (error()) {
        <app-list-error-state [message]="error()!" (retry)="cargar()" />
      } @else if (solicitudes().length === 0) {
        <app-list-empty-state
          message="No hay solicitudes pendientes de aprobación."
          icon="circle-check"
        />
      } @else {
        <ul class="grid gap-3">
          @for (s of solicitudes(); track s.idpartner) {
            <li
              class="rounded-lg border border-border-default bg-bg-surface p-5"
              [attr.data-testid]="'solicitud-' + s.idpartner"
            >
              <div class="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p class="m-0 font-semibold text-text-primary">{{ s.nombrepartner }}</p>
                  <p class="mt-1 text-sm text-text-secondary">Plan {{ s.planapi }}</p>
                </div>

                @if (puedeResolver) {
                  <div class="flex flex-wrap gap-2">
                    <button
                      type="button"
                      [attr.data-testid]="'btn-aprobar-' + s.idpartner"
                      class="rounded-lg bg-accent-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                      [disabled]="resolviendo()"
                      (click)="pedirConfirmacionAprobar(s)"
                    >
                      {{ resolviendo() ? 'Aprobando…' : 'Aprobar' }}
                    </button>
                    <button
                      type="button"
                      [attr.data-testid]="'btn-rechazar-' + s.idpartner"
                      class="rounded-lg border border-alert-critical px-4 py-2 text-sm font-medium text-alert-critical disabled:opacity-50"
                      [disabled]="resolviendo()"
                      (click)="abrirRechazo(s)"
                    >
                      Rechazar
                    </button>
                  </div>
                }
              </div>

              <!-- Confirmación en 2 pasos para aprobar (design-system § 5) -->
              @if (aprobandoA()?.idpartner === s.idpartner) {
                <div
                  class="mt-4 rounded-md border border-accent-primary p-4"
                  [attr.data-testid]="'confirmar-aprobar-' + s.idpartner"
                >
                  <p class="m-0 text-sm text-text-primary">
                    Al aprobar, el partner pasará a «Producción activa» y podrá emitir su
                    credencial productiva desde su portal.
                    <strong>El secreto no se te mostrará a ti</strong>: lo verá únicamente el
                    partner al emitirla.
                  </p>
                  <div class="mt-3 flex gap-2">
                    <button
                      type="button"
                      [attr.data-testid]="'btn-confirmar-aprobar-' + s.idpartner"
                      class="rounded-lg bg-accent-primary px-4 py-2 text-sm font-medium text-white"
                      (click)="aprobar(s)"
                    >
                      Confirmar aprobación
                    </button>
                    <button
                      type="button"
                      class="rounded-lg border border-border-default px-4 py-2 text-sm font-medium text-text-secondary"
                      (click)="cancelar()"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              }

              <!-- Rechazo: mensaje redactado, no un código de catálogo -->
              @if (rechazandoA()?.idpartner === s.idpartner) {
                <form
                  [formGroup]="formRechazo"
                  (ngSubmit)="rechazar(s)"
                  class="mt-4 rounded-md border border-alert-critical p-4"
                  [attr.data-testid]="'form-rechazo-' + s.idpartner"
                >
                  <label class="mb-1 block text-sm font-medium text-text-secondary" for="motivo">
                    Motivo del rechazo
                  </label>
                  <textarea
                    id="motivo"
                    rows="3"
                    data-testid="input-motivo"
                    [class]="inputClass"
                    formControlName="motivo"
                  ></textarea>
                  <p class="mt-1 text-xs text-text-secondary">
                    Este texto se envía al contacto técnico del partner: es lo que le permitirá
                    corregir. Mínimo {{ motivoMinimo }} caracteres
                    ({{ largoMotivo() }}/{{ motivoMinimo }}).
                  </p>
                  @if (motivoInvalido()) {
                    <p class="mt-1 text-xs text-alert-critical" data-testid="error-motivo">
                      Escribe un motivo de al menos {{ motivoMinimo }} caracteres.
                    </p>
                  }
                  <div class="mt-3 flex gap-2">
                    <button
                      type="submit"
                      [attr.data-testid]="'btn-confirmar-rechazo-' + s.idpartner"
                      class="rounded-lg bg-alert-critical px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                      [disabled]="formRechazo.invalid || resolviendo()"
                    >
                      {{ resolviendo() ? 'Rechazando…' : 'Confirmar rechazo' }}
                    </button>
                    <button
                      type="button"
                      class="rounded-lg border border-border-default px-4 py-2 text-sm font-medium text-text-secondary"
                      (click)="cancelar()"
                    >
                      Cancelar
                    </button>
                  </div>
                </form>
              }
            </li>
          }
        </ul>
      }
    </section>
  `,
})
export class ColaSolicitudesPage implements OnInit {
  private readonly api = inject(PartnerApiService);
  private readonly auth = inject(AuthApiService);
  private readonly fb = inject(FormBuilder);

  readonly solicitudes = signal<PartnerListItem[]>([]);
  readonly cargando = signal(true);
  readonly resolviendo = signal(false);
  readonly error = signal<string | null>(null);
  readonly errorAccion = signal<string | null>(null);
  readonly confirmacion = signal<string | null>(null);
  readonly avisoConcurrencia = signal(false);
  readonly aprobandoA = signal<PartnerListItem | null>(null);
  readonly rechazandoA = signal<PartnerListItem | null>(null);

  readonly shellClass = LIST_PAGE_SHELL_CLASS;
  readonly motivoMinimo = MOTIVO_MINIMO;
  readonly inputClass =
    'w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary';

  readonly formRechazo = this.fb.nonNullable.group({
    motivo: ['', [Validators.required, Validators.minLength(MOTIVO_MINIMO)]],
  });

  /** Solo el Administrador resuelve; el Desarrollador de APIs mira (FR-UI-011). */
  readonly puedeResolver = this.auth.hasRole(ROL_RESUELVE_PROMOCION);

  ngOnInit(): void {
    this.cargar();
  }

  largoMotivo(): number {
    return this.formRechazo.getRawValue().motivo.trim().length;
  }

  motivoInvalido(): boolean {
    const control = this.formRechazo.controls.motivo;
    return control.invalid && control.touched;
  }

  /** La cola se deriva del listado filtrado: no hace falta endpoint nuevo. */
  cargar(): void {
    this.cargando.set(true);
    this.error.set(null);
    this.api.listar({ estado: ESTADO_PENDIENTE_APROBACION, limit: 50 }).subscribe({
      next: (res) => {
        this.solicitudes.set(res.data);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar las solicitudes pendientes.');
        this.cargando.set(false);
      },
    });
  }

  pedirConfirmacionAprobar(s: PartnerListItem): void {
    this.rechazandoA.set(null);
    this.aprobandoA.set(s);
  }

  abrirRechazo(s: PartnerListItem): void {
    this.aprobandoA.set(null);
    this.formRechazo.reset();
    this.rechazandoA.set(s);
  }

  cancelar(): void {
    this.aprobandoA.set(null);
    this.rechazandoA.set(null);
  }

  aprobar(s: PartnerListItem): void {
    this.resolver(s, { decision: 'aprobar' }, `Promoción de ${s.nombrepartner} aprobada. El partner emitirá su credencial de producción desde su portal.`);
  }

  rechazar(s: PartnerListItem): void {
    if (this.formRechazo.invalid) {
      this.formRechazo.controls.motivo.markAsTouched();
      return;
    }
    const motivo = this.formRechazo.getRawValue().motivo.trim();
    this.resolver(
      s,
      { decision: 'rechazar', motivo },
      `Solicitud de ${s.nombrepartner} rechazada. El motivo se envió a su contacto técnico.`,
    );
  }

  private resolver(
    s: PartnerListItem,
    cuerpo: { decision: 'aprobar' | 'rechazar'; motivo?: string },
    mensajeExito: string,
  ): void {
    this.resolviendo.set(true);
    this.errorAccion.set(null);
    this.avisoConcurrencia.set(false);
    const devolverControl = setTimeout(() => this.resolviendo.set(false), TIMEOUT_ACCION_MS);

    this.api.resolverPromocion(s.idpartner, cuerpo, nuevaClaveIdempotencia()).subscribe({
      next: () => {
        clearTimeout(devolverControl);
        this.resolviendo.set(false);
        this.cancelar();
        // Deliberadamente NO se muestra el secreto de la credencial productiva
        // aunque el backend lo devuelva: no es de quien aprueba (FR-UI-009).
        this.confirmacion.set(mensajeExito);
        this.cargar();
      },
      error: (err) => {
        clearTimeout(devolverControl);
        this.resolviendo.set(false);
        const code = String((err as { error?: { code?: string } })?.error?.code ?? '');
        if (code === 'sin_solicitud_pendiente') {
          // Dos administradores a la vez. No es culpa del usuario, así que el
          // copy no lo culpa y la cola se refresca sola.
          this.cancelar();
          this.avisoConcurrencia.set(true);
          this.cargar();
          return;
        }
        this.errorAccion.set(
          code === 'motivo_requerido'
            ? 'El rechazo exige un motivo, que se envía al partner.'
            : 'No se pudo resolver la solicitud.',
        );
      },
    });
  }
}
