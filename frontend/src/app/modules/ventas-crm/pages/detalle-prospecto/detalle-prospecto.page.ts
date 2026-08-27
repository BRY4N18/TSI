import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { crmBadge } from '../../crm-ui';
import {
  AsignacionProspecto,
  EtapaPipeline,
  Prospecto,
  TipoCliente,
  TransicionPipeline,
} from '../../models/prospectos.types';
import { ConversionApiService } from '../../services/conversion-api.service';
import { PipelineApiService } from '../../services/pipeline-api.service';
import { ProspectoApiService } from '../../services/prospecto-api.service';

const NEXT: Partial<Record<EtapaPipeline, Exclude<EtapaPipeline, 'Nuevo' | 'Ganado' | 'Perdido'>>> =
  {
    Nuevo: 'Contactado',
    Contactado: 'Calificado',
    Calificado: 'Propuesta',
    Propuesta: 'Negociación',
  };

@Component({
  selector: 'app-detalle-prospecto',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    TablerIconComponent,
    ListLoadingSkeletonComponent,
    ListErrorStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="mx-auto max-w-6xl p-8">
      <a
        routerLink="/ventas-crm/prospectos"
        class="mb-6 inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary no-underline hover:text-text-primary"
      >
        <app-tabler-icon name="arrow-left" [size]="16" />
        Volver a la lista
      </a>

      @if (loading()) {
        <app-list-loading-skeleton [count]="3" />
      } @else if (error()) {
        <app-list-error-state [message]="error()!" (retry)="cargar()" />
      } @else if (prospecto()) {
        @let p = prospecto()!;
        <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
          <div class="min-w-0">
            <p class="m-0 text-sm font-medium text-text-secondary">Detalles</p>
            <div class="mt-1 flex flex-wrap items-center gap-3">
              <h1 class="tsi-display m-0 text-2xl font-bold text-text-primary" data-testid="workpanel-titulo">
                {{ p.nombres }} {{ p.apellidos }}
              </h1>
<div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>
              <span [class]="etapaBadge(p.etapa_actual)">{{ p.etapa_actual }}</span>
              <span [class]="p.activo ? okBadge() : warnBadge()">
                {{ p.activo ? 'Activo' : 'Inactivo' }}
              </span>
            </div>
          </div>
        </div>

        <div class="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div class="grid gap-4 lg:col-span-2">
            <section class="rounded-md border border-border-default bg-bg-surface p-6">
              <h2 class="m-0 mb-4 text-base font-semibold text-text-primary">
                Información del prospecto
              </h2>
              <dl class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">
                    Empresa
                  </dt>
                  <dd class="mt-1 text-sm text-text-primary">{{ p.empresa }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">
                    Organización
                  </dt>
                  <dd class="mt-1 text-sm text-text-primary">{{ p.tipo_organizacion }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">
                    Email
                  </dt>
                  <dd class="mt-1 text-sm text-text-primary">{{ p.gmail }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">
                    Teléfono
                  </dt>
                  <dd class="mt-1 text-sm text-text-primary">{{ p.telefono }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">
                    Cargo
                  </dt>
                  <dd class="mt-1 text-sm text-text-primary">{{ p.cargo }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-medium uppercase tracking-wide text-text-secondary">
                    Cómo nos conoció
                  </dt>
                  <dd class="mt-1 text-sm text-text-primary">{{ p.como_nos_conocio }}</dd>
                </div>
              </dl>
            </section>

            @if (p.activo) {
              <section class="rounded-md border border-border-default bg-bg-surface p-6">
                <h2 class="m-0 mb-4 text-base font-semibold text-text-primary">Acciones</h2>
                <div class="flex flex-wrap gap-2">
                  @if (nextEtapa()) {
                    <button
                      type="button"
                      data-testid="btn-avanzar-etapa"
                      class="inline-flex min-h-11 items-center gap-2 rounded-md bg-accent-primary px-4 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-60"
                      [disabled]="busy()"
                      (click)="avanzar()"
                    >
                      <app-tabler-icon name="chevron-right" [size]="16" />
                      Avanzar a {{ nextEtapa() }}
                    </button>
                  }
                  <button
                    type="button"
                    data-testid="btn-pedir-perdido"
                    class="inline-flex min-h-11 items-center gap-2 rounded-md border border-alert-critical px-4 text-sm font-medium text-alert-critical hover:bg-alert-critical-bg disabled:opacity-60"
                    [disabled]="busy()"
                    (click)="pedirPerdido()"
                  >
                    <app-tabler-icon name="x" [size]="16" />
                    Marcar perdido
                  </button>
                </div>

                @if (esAdmin() && p.idusuario == null) {
                  <form
                    class="mt-6 grid max-w-md gap-3 border-t border-border-default pt-6"
                    [formGroup]="asigForm"
                    (ngSubmit)="asignar()"
                  >
                    <p class="m-0 text-sm font-medium text-text-primary">
                      Asignación de huérfano
                    </p>
                    <p class="m-0 text-sm text-text-secondary">
                      Se asignará a tu sesión:
                      <span class="font-medium text-text-primary">{{ gerenteLabel() }}</span>
                    </p>
                    <label class="grid gap-1.5 text-sm font-medium text-text-secondary">
                      Motivo
                      <input
                        formControlName="motivo"
                        class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
          placeholder="Motivo, en una frase"
        />
                    </label>
                    <button
                      type="submit"
                      data-testid="btn-asignar"
                      class="inline-flex min-h-11 w-fit items-center gap-2 rounded-md border border-border-default px-4 text-sm font-medium hover:bg-bg-page disabled:opacity-60"
                      [disabled]="busy() || asigForm.invalid"
                    >
                      Asignarme este prospecto
                    </button>
                  </form>
                }

                @if (p.etapa_actual === 'Negociación') {
                  <form
                    class="mt-6 grid max-w-md gap-3 border-t border-border-default pt-6"
                    [formGroup]="convForm"
                    (ngSubmit)="convertir()"
                  >
                    <p class="m-0 text-sm font-medium text-text-primary">Convertir a cliente</p>
                    <label class="grid gap-1.5 text-sm font-medium text-text-secondary">
                      Tipo
                      <select
                        formControlName="tipo"
                        class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
                      >
                        <option value="Aseguradora">Aseguradora</option>
                        <option value="Municipio">Municipio</option>
                        <option value="Proveedor">Proveedor</option>
                        <option value="Smart City">Smart City</option>
                      </select>
                    </label>
                    <label class="grid gap-1.5 text-sm font-medium text-text-secondary">
                      NIT
                      <input
                        formControlName="nit_identificacion"
                        class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
          placeholder="RFC o identificación fiscal"
        />
                    </label>
                    <button
                      type="submit"
                      data-testid="btn-convertir"
                      class="inline-flex min-h-11 w-fit items-center gap-2 rounded-md bg-accent-primary px-4 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-60"
                      [disabled]="busy() || convForm.invalid"
                    >
                      <app-tabler-icon name="circle-check" [size]="16" />
                      Convertir
                    </button>
                  </form>
                }
              </section>
            }

            @if (actionError()) {
              <div
                class="flex flex-wrap items-center gap-3 rounded-md border border-alert-warning bg-alert-warning-bg p-4"
                role="alert"
              >
                <app-tabler-icon name="alert-triangle" [size]="20" />
                <p class="m-0 flex-1 text-sm text-alert-warning">{{ actionError() }}</p>
                <button
                  type="button"
                  data-testid="btn-refrescar-prospecto"
                  class="inline-flex min-h-11 items-center gap-2 rounded-md border border-alert-warning px-4 text-sm font-medium text-alert-warning hover:bg-alert-warning/10"
                  (click)="cargar()"
                >
                  <app-tabler-icon name="refresh" [size]="16" />
                  Refrescar
                </button>
              </div>
            }
          </div>

          <div class="grid gap-4">
            <section class="rounded-md border border-border-default bg-bg-surface p-6">
              <h2 class="m-0 mb-3 text-base font-semibold text-text-primary">Resumen</h2>
              <dl class="grid gap-3 text-sm">
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Etapa</dt>
                  <dd class="font-medium text-text-primary">{{ p.etapa_actual }}</dd>
                </div>
                <div class="flex justify-between gap-2">
                  <dt class="text-text-secondary">Estado</dt>
                  <dd class="font-medium text-text-primary">
                    {{ p.activo ? 'Activo' : 'Inactivo' }}
                  </dd>
                </div>
                @if (p.motivo_inactividad) {
                  <div class="flex justify-between gap-2">
                    <dt class="text-text-secondary">Motivo</dt>
                    <dd class="font-medium text-text-primary">{{ p.motivo_inactividad }}</dd>
                  </div>
                }
              </dl>
            </section>

            <!--
              Rastro del prospecto. El detalle ya devolvía ambos historiales
              (RF-CPP-008) y la pantalla los descartaba, así que no había forma
              de ver quién lo tuvo ni por qué etapas pasó — y cada acción parecía
              no dejar huella (hallazgo #14).
            -->
            <section class="rounded-md border border-border-default bg-bg-surface p-6">
              <h2 class="m-0 mb-3 text-base font-semibold text-text-primary">Historial de etapas</h2>
              @if (historialPipeline().length) {
                <ol class="m-0 grid list-none gap-3 p-0" data-testid="historial-pipeline">
                  @for (t of historialPipelineReciente(); track t.id_transicion) {
                    <li class="border-l-2 border-border-default pl-3">
                      <p class="m-0 text-sm font-medium text-text-primary">
                        {{ t.etapa_anterior ?? '—' }} → {{ t.etapa_nueva }}
                      </p>
                      @if (t.fecha_transicion) {
                        <p class="m-0 text-xs text-text-secondary">
                          {{ t.fecha_transicion | date: 'dd/MM/yyyy HH:mm' }}
                        </p>
                      }
                      @if (t.motivo_perdida) {
                        <p class="m-0 text-xs text-text-secondary">Motivo: {{ t.motivo_perdida }}</p>
                      }
                    </li>
                  }
                </ol>
              } @else {
                <p class="m-0 text-sm text-text-secondary">Sin cambios de etapa registrados.</p>
              }
            </section>

            <section class="rounded-md border border-border-default bg-bg-surface p-6">
              <h2 class="m-0 mb-3 text-base font-semibold text-text-primary">
                Historial de asignación
              </h2>
              @if (historialAsignacion().length) {
                <ol class="m-0 grid list-none gap-3 p-0" data-testid="historial-asignacion">
                  @for (a of historialAsignacionReciente(); track a.idasignacion) {
                    <li class="border-l-2 border-border-default pl-3">
                      <p class="m-0 text-sm font-medium text-text-primary">
                        {{ a.idusuariogerenteanterior ?? 'Sin dueño' }} →
                        {{ a.idusuariogerenteactual }}
                        <span class="text-text-secondary">({{ a.tipoasignacion }})</span>
                      </p>
                      @if (a.fechahoraasignacion) {
                        <p class="m-0 text-xs text-text-secondary">
                          {{ a.fechahoraasignacion | date: 'dd/MM/yyyy HH:mm' }}
                        </p>
                      }
                      @if (a.motivo) {
                        <p class="m-0 text-xs text-text-secondary">Motivo: {{ a.motivo }}</p>
                      }
                    </li>
                  }
                </ol>
              } @else {
                <p class="m-0 text-sm text-text-secondary">Sin reasignaciones registradas.</p>
              }
            </section>
          </div>
        </div>
      }
    </div>

    @if (mostrarPerdido()) {
      <div
        class="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="perdido-title"
      >
        <div class="w-full max-w-md tsi-panel tsi-panel--elevado p-6">
          <h2 id="perdido-title" class="m-0 mb-2 text-lg font-semibold text-text-primary">
            Marcar como perdido
          </h2>
          <p class="m-0 mb-4 text-sm text-text-secondary">El motivo es obligatorio.</p>
          <form [formGroup]="perdidaForm" (ngSubmit)="confirmarPerdido()" class="grid gap-3">
            <label class="grid gap-1.5 text-sm font-medium text-text-secondary">
              Motivo
              <input
                formControlName="motivo_perdida"
                data-testid="input-motivo-perdida"
                class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
          placeholder="Motivo, en una frase"
        />
            </label>
            <div class="flex flex-wrap justify-end gap-2">
              <button
                type="button"
                class="inline-flex min-h-11 items-center justify-center rounded-md border border-border-default px-4 text-sm font-medium hover:bg-bg-page"
                (click)="cancelarPerdido()"
              >
                Cancelar
              </button>
              <button
                type="submit"
                data-testid="btn-confirmar-perdido"
                class="inline-flex min-h-11 items-center justify-center rounded-md border border-alert-critical px-4 text-sm font-medium text-alert-critical hover:bg-alert-critical-bg disabled:opacity-55"
                [disabled]="busy() || perdidaForm.invalid"
              >
                Confirmar
              </button>
            </div>
          </form>
        </div>
      </div>
    }
  `,
})
export class DetalleProspectoPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly prospectoApi = inject(ProspectoApiService);
  private readonly pipelineApi = inject(PipelineApiService);
  private readonly conversionApi = inject(ConversionApiService);
  private readonly auth = inject(AuthApiService);
  private readonly notifications = inject(NotificationService);
  private readonly fb = inject(FormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);

  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly actionError = signal<string | null>(null);
  readonly prospecto = signal<Prospecto | null>(null);
  /**
   * Rastro del prospecto. Se guarda aparte de `prospecto` a propósito: las
   * respuestas de las acciones (transición, asignación) devuelven el prospecto
   * actualizado **sin** los historiales, así que meterlos en la misma señal los
   * borraría en cuanto se ejecutara cualquier acción.
   *
   * En vez de recargar del servidor —Pinot tiene retraso de lectura tras
   * escritura y devolvería el estado anterior— se **añade** la fila que la
   * propia acción acaba de devolver.
   */
  readonly historialPipeline = signal<TransicionPipeline[]>([]);
  readonly historialAsignacion = signal<AsignacionProspecto[]>([]);
  readonly esAdmin = signal(false);
  readonly mostrarPerdido = signal(false);

  readonly perdidaForm = this.fb.nonNullable.group({
    motivo_perdida: ['', Validators.required],
  });
  readonly convForm = this.fb.nonNullable.group({
    tipo: ['Aseguradora' as TipoCliente, Validators.required],
    nit_identificacion: ['', Validators.required],
  });
  readonly asigForm = this.fb.nonNullable.group({
    motivo: ['', Validators.required],
  });

  private id = 0;
  private gerenteId = 0;
  private gerenteGmail = '';

  ngOnInit(): void {
    this.esAdmin.set(this.auth.hasRole('Administrador'));
    const profile = this.auth.getProfile();
    if (profile?.idusuario) {
      this.gerenteId = profile.idusuario;
      this.gerenteGmail = profile.gmail;
    }
    this.id = Number(this.route.snapshot.paramMap.get('idprospecto'));
    this.cargar();
  }

  gerenteLabel(): string {
    return this.gerenteGmail || 'tu usuario';
  }

  /** Más recientes arriba: el rastro se lee de lo último hacia atrás. */
  historialPipelineReciente(): TransicionPipeline[] {
    return [...this.historialPipeline()].reverse();
  }

  historialAsignacionReciente(): AsignacionProspecto[] {
    return [...this.historialAsignacion()].reverse();
  }

  /**
   * Añade al rastro la fila que la propia acción acaba de devolver.
   *
   * No se recarga del servidor a propósito: `Fact_Pipeline` y `Fact_Asignacion`
   * se escriben por Kafka y Pinot tarda en ingerirlas, así que un `GET`
   * inmediato devolvería el historial **sin** la fila recién creada — que es
   * justo la que el usuario acaba de provocar y espera ver.
   */
  private registrarTransicionLocal(transicion: TransicionPipeline | undefined): void {
    if (transicion) {
      this.historialPipeline.update((h) => [...h, transicion]);
    }
  }

  private registrarAsignacionLocal(asignacion: AsignacionProspecto | undefined): void {
    if (asignacion) {
      this.historialAsignacion.update((h) => [...h, asignacion]);
    }
  }

  nextEtapa(): string | null {
    const p = this.prospecto();
    if (!p) return null;
    return NEXT[p.etapa_actual] ?? null;
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(null);
    this.actionError.set(null);
    this.prospectoApi.obtener(this.id).subscribe({
      next: (res) => {
        this.prospecto.set(res.data);
        this.historialPipeline.set(res.data.historial_pipeline ?? []);
        this.historialAsignacion.set(res.data.historial_asignacion ?? []);
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'No se pudo cargar');
        this.loading.set(false);
        this.cdr.markForCheck();
      },
    });
  }

  avanzar(): void {
    const p = this.prospecto();
    const next = this.nextEtapa() as
      | 'Contactado'
      | 'Calificado'
      | 'Propuesta'
      | 'Negociación'
      | null;
    if (!p || !next) return;
    this.busy.set(true);
    this.actionError.set(null);
    this.pipelineApi
      .registrarTransicion(p.idprospecto, {
        etapa_nueva: next,
        etapa_actual_esperada: p.etapa_actual,
      })
      .subscribe({
        next: (res) => {
          this.prospecto.set(res.data.prospecto);
          this.registrarTransicionLocal(res.data.transicion);
          this.busy.set(false);
          this.notifications.toast('Etapa actualizada.', 'success');
          this.cdr.markForCheck();
        },
        error: (err) => this.handleActionError(err, 'Conflicto o error de transición'),
      });
  }

  pedirPerdido(): void {
    this.perdidaForm.reset({ motivo_perdida: '' });
    this.mostrarPerdido.set(true);
  }

  cancelarPerdido(): void {
    this.mostrarPerdido.set(false);
  }

  confirmarPerdido(): void {
    const p = this.prospecto();
    if (!p || this.perdidaForm.invalid) return;
    this.busy.set(true);
    this.pipelineApi
      .registrarTransicion(p.idprospecto, {
        etapa_nueva: 'Perdido',
        etapa_actual_esperada: p.etapa_actual,
        motivo_perdida: this.perdidaForm.controls.motivo_perdida.value,
      })
      .subscribe({
        next: (res) => {
          this.prospecto.set(res.data.prospecto);
          this.registrarTransicionLocal(res.data.transicion);
          this.busy.set(false);
          this.mostrarPerdido.set(false);
          this.notifications.toast('Prospecto marcado como perdido.', 'success');
          this.cdr.markForCheck();
        },
        error: (err) => this.handleActionError(err, 'No se pudo marcar perdido'),
      });
  }

  asignar(): void {
    const p = this.prospecto();
    if (!p || this.asigForm.invalid || !this.esAdmin() || this.gerenteId < 1) return;
    this.busy.set(true);
    this.prospectoApi
      .asignar(p.idprospecto, {
        idusuariogerenteactual: this.gerenteId,
        motivo: this.asigForm.controls.motivo.value,
        // Dueño vigente según lo que esta pantalla tiene cargado. Sin él el
        // backend comparaba `undefined` contra el dueño real y devolvía 409
        // "Asignación desactualizada" en todo prospecto ya asignado, así que la
        // reasignación no se aplicaba nunca (hallazgo #14).
        idusuario_esperado: p.idusuario ?? null,
      })
      .subscribe({
        next: (res) => {
          this.prospecto.set(res.data.prospecto);
          this.registrarAsignacionLocal(res.data.asignacion);
          this.busy.set(false);
          this.notifications.toast('Asignación aplicada.', 'success');
          this.cdr.markForCheck();
        },
        error: (err) => this.handleActionError(err, 'No se pudo asignar'),
      });
  }

  convertir(): void {
    const p = this.prospecto();
    if (!p || this.convForm.invalid) return;
    this.busy.set(true);
    const v = this.convForm.getRawValue();
    this.conversionApi
      .convertir(
        p.idprospecto,
        {
          tipo: v.tipo,
          nit_identificacion: v.nit_identificacion,
          etapa_actual_esperada: 'Negociación',
        },
        crypto.randomUUID(),
      )
      .subscribe({
        next: (res) => {
          this.prospecto.set(res.data.prospecto);
          this.busy.set(false);
          this.notifications.toast('Conversión completada.', 'success');
          this.cdr.markForCheck();
        },
        error: (err) => this.handleActionError(err, 'Conversión fallida'),
      });
  }

  etapaBadge(etapa: string): string {
    if (etapa === 'Perdido') return crmBadge('danger');
    if (etapa === 'Ganado') return crmBadge('ok');
    if (etapa === 'Negociación' || etapa === 'Propuesta') return crmBadge('warn');
    return crmBadge('info');
  }

  okBadge(): string {
    return crmBadge('ok');
  }

  warnBadge(): string {
    return crmBadge('warn');
  }

  private handleActionError(
    err: { status?: number; error?: { detail?: string } },
    fallback: string,
  ): void {
    this.busy.set(false);
    this.mostrarPerdido.set(false);
    const detail = err?.error?.detail ?? fallback;
    this.actionError.set(detail);
    this.notifications.toast(detail, err?.status === 409 ? 'warning' : 'critical');
    // 409: dejar mensaje + botón Refrescar (no auto-cargar: limpiaría actionError).
    this.cdr.markForCheck();
  }
}
