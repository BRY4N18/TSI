import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../shared/ui/list-states/list-table.styles';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { ConfirmDialogService } from '../../../../shared/notifications/confirm-dialog.service';
import { presentacionDe } from '../../estado-partner.constants';
import { presentacionEntorno } from '../../entorno.constants';
import {
  PartnerApiService,
  nuevaClaveIdempotencia,
} from '../../services/partner-api.service';
import {
  estaSuspendido,
  formatearCupo,
  formatearPlan,
  formatearVigencia,
} from '../../services/models/centinelas';
import type { CredencialItem, PartnerDetalle } from '../../services/models/partner.types';

type Modo = 'ver' | 'crear';

/** Copy de cada fallo de negocio. Un `code` sin entrada aquí sería un
 *  «error inesperado», que es justo lo que SC-005 prohíbe. */
const COPY_ERROR: Record<string, string> = {
  validation_error: 'Revisa los campos marcados.',
  not_found: 'El cliente indicado no existe.',
  sin_suscripcion:
    'El cliente no tiene una suscripción vigente. Debe resolverse en Suscripciones antes de registrar el partner.',
  plan_incompleto:
    'El plan contratado no declara sus límites de API. Debe corregirse en el catálogo de planes.',
};

/**
 * Workpanel del partner — página dedicada, variante **Ver-only** del
 * design-system (FR-UI-003).
 *
 * Dos modos: Ver y Crear. No hay Editar porque el backend no expone PATCH de
 * ficha; un modo de edición sin endpoint sería una promesa que la UI no puede
 * cumplir.
 */
@Component({
  selector: 'app-detalle-partner',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    TablerIconComponent,
    ListErrorStateComponent,
    ListLoadingSkeletonComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <!-- Chrome del golden sample: volver, eyebrow, h1 + badge -->
      <a
        routerLink="/partners/consola"
        data-testid="link-volver"
        class="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-accent-primary hover:underline"
      >
        <app-tabler-icon name="arrow-left" [size]="16" />
        Volver a la lista
      </a>

      <p class="m-0 text-xs font-medium uppercase tracking-wide text-text-secondary">
        {{ modo === 'crear' ? 'Nuevo partner' : 'Detalles' }}
      </p>

      @if (cargando()) {
        <app-list-loading-skeleton [count]="4" />
      } @else if (errorCarga()) {
        <app-list-error-state [message]="errorCarga()!" (retry)="cargar()" />
      } @else if (modo === 'crear') {
        <h1 class="tsi-display mb-6 mt-1 text-3xl font-extrabold text-text-primary">Nuevo partner</h1>
<div class="tsi-rail-h mt-2 w-24" aria-hidden="true"></div>

        @if (errorAccion()) {
          <div
            class="mb-4 rounded-md border border-alert-critical bg-alert-critical-bg p-4 text-sm text-alert-critical"
            data-testid="banner-error"
            role="alert"
          >
            {{ errorAccion() }}
            @if (idpartnerDuplicado()) {
              <a
                [routerLink]="['/partners/consola', idpartnerDuplicado()]"
                data-testid="link-partner-existente"
                class="ml-2 font-medium underline"
              >
                Ver el partner existente
              </a>
            }
          </div>
        }

        <form [formGroup]="form" (ngSubmit)="guardar()" class="grid max-w-2xl gap-5">
          <div class="tsi-panel p-6">
            <h2 class="tsi-display m-0 mb-4 text-lg font-semibold text-text-primary">Identificación</h2>

            <label class="mb-1 block text-sm font-medium text-text-secondary" for="cliente">
              Cliente
            </label>
            <!-- Se elige por NOMBRE legible: está prohibido pedir el id (FR-UI-004). -->
            <select id="cliente" data-testid="input-cliente" [class]="inputClass" formControlName="idcliente">
              <option [ngValue]="null">Selecciona un cliente…</option>
              @for (c of clientes(); track c.idcliente) {
                <option [ngValue]="c.idcliente">{{ c.nombre }}</option>
              }
            </select>

            <label class="mb-1 mt-4 block text-sm font-medium text-text-secondary" for="nombre">
              Nombre del partner
            </label>
            <input id="nombre" data-testid="input-nombre" [class]="inputClass" formControlName="nombrepartner" />
          </div>

          <div class="tsi-panel p-6">
            <h2 class="tsi-display m-0 mb-4 text-lg font-semibold text-text-primary">Contacto técnico</h2>
            <p class="mb-4 text-sm text-text-secondary">
              Recibirá los avisos de credenciales y de la promoción a producción.
            </p>

            <label class="mb-1 block text-sm font-medium text-text-secondary" for="contacto">
              Nombre
            </label>
            <input id="contacto" data-testid="input-contacto" [class]="inputClass" formControlName="contacto_tecnico_nombre" />

            <label class="mb-1 mt-4 block text-sm font-medium text-text-secondary" for="gmail">
              Correo
            </label>
            <input id="gmail" type="email" data-testid="input-gmail" [class]="inputClass" formControlName="contacto_tecnico_gmail" />
          </div>

          <div>
            <button
              type="submit"
              data-testid="btn-guardar"
              class="tsi-btn tsi-btn-primary"
              [disabled]="form.invalid || guardando()"
            >
              {{ guardando() ? 'Guardando…' : 'Guardar' }}
            </button>
          </div>
        </form>
      } @else {
        <!-- El alias "as" solo se admite en el @if primario, no en un @else if -->
        @if (partner(); as p) {
        <div class="mb-6 mt-1 flex flex-wrap items-center gap-3">
          <h1 class="tsi-display m-0 text-3xl font-extrabold text-text-primary">{{ p.nombrepartner }}</h1>
          <span
            class="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium"
            [class]="presentacion(p.estado).tono"
            data-testid="badge-estado"
          >
            <app-tabler-icon [name]="presentacion(p.estado).icono" [size]="14" />
            {{ p.estado }}
          </span>
        </div>

        @if (errorAccion()) {
          <div class="mb-4 rounded-md border border-alert-critical bg-alert-critical-bg p-4 text-sm text-alert-critical" role="alert">
            {{ errorAccion() }}
          </div>
        }

        <!-- Modo Ver: <dl>, nunca <input disabled> (design-system § 5) -->
        <div class="grid gap-5 md:grid-cols-2">
          <section class="tsi-panel p-6">
            <h2 class="tsi-display m-0 mb-4 text-lg font-semibold text-text-primary">Identificación</h2>
            <dl class="grid grid-cols-[auto_1fr] gap-x-6 gap-y-3 text-sm" data-testid="dl-identificacion">
              <dt class="text-xs uppercase tracking-wide text-text-secondary">Contacto técnico</dt>
              <dd class="m-0 text-text-primary">{{ p.contacto_tecnico_nombre }}</dd>
              <dt class="text-xs uppercase tracking-wide text-text-secondary">Correo</dt>
              <dd class="m-0 text-text-primary">{{ p.contacto_tecnico_gmail }}</dd>
            </dl>
          </section>

          <section class="tsi-panel p-6">
            <h2 class="tsi-display m-0 mb-4 text-lg font-semibold text-text-primary">Plan y cupo</h2>
            <dl class="grid grid-cols-[auto_1fr] gap-x-6 gap-y-3 text-sm">
              <dt class="text-xs uppercase tracking-wide text-text-secondary">Plan</dt>
              <dd class="m-0 text-text-primary" data-testid="dd-plan">{{ plan(p) }}</dd>
              <dt class="text-xs uppercase tracking-wide text-text-secondary">Llamadas / mes</dt>
              <dd class="m-0 text-text-primary" data-testid="dd-cupo-mes">{{ cupoMes(p) }}</dd>
              <dt class="text-xs uppercase tracking-wide text-text-secondary">Llamadas / minuto</dt>
              <dd class="m-0 text-text-primary">{{ cupoMinuto(p) }}</dd>
            </dl>

            <!-- Acción de dominio: depende de ESTADO y ROL, no del modo. -->
            @if (puedeAsignarPlan(p)) {
              <div class="mt-5 border-t border-border-default pt-4">
                <p class="mb-3 text-sm text-text-secondary">
                  El cupo se deriva del plan contratado por el cliente y queda
                  <strong>congelado</strong>: un cambio posterior de su plan no lo alterará.
                </p>
                <button
                  type="button"
                  data-testid="btn-asignar-plan"
                  class="tsi-btn tsi-btn-primary"
                  [disabled]="asignando()"
                  (click)="asignarPlan(p)"
                >
                  {{ asignando() ? 'Asignando…' : 'Asignar plan de acceso' }}
                </button>
              </div>
            }

            <!-- RF-PAC-005: el Administrador suspende o reactiva por causas
                 distintas a la mora —vencimiento de contrato, petición del
                 cliente—. El panel de suspensiones solo lista suspendidos y
                 morosos, así que la acción tiene que vivir también aquí, donde
                 está cualquier partner. -->
            @if (esAdministrador()) {
              <div class="mt-5 border-t border-border-default pt-4">
                @if (suspendido(p)) {
                  <p class="mb-3 text-sm text-text-secondary">
                    Al reactivar se restituyen solo las credenciales que estaban activas antes
                    de la suspensión; las que el partner revocó por seguridad seguirán inactivas.
                  </p>
                  <button
                    type="button"
                    data-testid="btn-reactivar"
                    class="tsi-btn tsi-btn-primary"
                    [disabled]="cambiandoAcceso()"
                    (click)="reactivar(p)"
                  >
                    {{ cambiandoAcceso() ? 'Reactivando…' : 'Reactivar acceso' }}
                  </button>
                } @else {
                  <p class="mb-3 text-sm text-text-secondary">
                    Suspender desactiva <strong>todas</strong> sus credenciales, de pruebas y de
                    producción. Se usa por mora, vencimiento de contrato o petición del cliente.
                  </p>
                  <button
                    type="button"
                    data-testid="btn-suspender"
                    class="tsi-btn border border-alert-critical bg-transparent text-alert-critical hover:bg-alert-critical-bg"
                    [disabled]="cambiandoAcceso()"
                    (click)="suspender(p)"
                  >
                    {{ cambiandoAcceso() ? 'Suspendiendo…' : 'Suspender acceso' }}
                  </button>
                }
                @if (mensajeAcceso()) {
                  <p class="mt-3 text-sm text-text-primary" data-testid="mensaje-acceso">
                    {{ mensajeAcceso() }}
                  </p>
                }
              </div>
            }
          </section>

          <section class="tsi-panel p-6 md:col-span-2">
            <h2 class="tsi-display m-0 mb-4 text-lg font-semibold text-text-primary">Credenciales</h2>
            @if (p.credenciales.length === 0) {
              <p class="m-0 text-sm text-text-secondary">Este partner aún no ha emitido credenciales.</p>
            } @else {
              <ul class="grid gap-2">
                @for (c of p.credenciales; track c.idcredencial) {
                  <li class="flex flex-wrap items-center gap-3 rounded-md border border-border-default p-3 text-sm">
                    <span
                      class="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium"
                      [class]="entorno(c).tono"
                    >
                      <app-tabler-icon [name]="entorno(c).icono" [size]="14" />
                      {{ entorno(c).etiqueta }}
                    </span>
                    <span class="font-medium text-text-primary">{{ c.nombre_credencial }}</span>
                    <span class="text-text-secondary">{{ vigencia(c) }}</span>
                  </li>
                }
              </ul>
            }
          </section>
        </div>
        }
      }
    </section>
  `,
})
export class DetallePartnerPage implements OnInit {
  private readonly api = inject(PartnerApiService);
  private readonly authApi = inject(AuthApiService);
  private readonly confirmDialog = inject(ConfirmDialogService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);

  readonly partner = signal<PartnerDetalle | null>(null);
  readonly clientes = signal<{ idcliente: number; nombre: string }[]>([]);
  readonly cargando = signal(false);
  readonly guardando = signal(false);
  readonly asignando = signal(false);
  readonly cambiandoAcceso = signal(false);
  readonly mensajeAcceso = signal<string | null>(null);
  readonly errorCarga = signal<string | null>(null);
  readonly errorAccion = signal<string | null>(null);
  readonly idpartnerDuplicado = signal<number | null>(null);

  modo: Modo = 'ver';
  readonly shellClass = LIST_PAGE_SHELL_CLASS;
  readonly inputClass =
    'w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary';

  readonly form = this.fb.nonNullable.group({
    idcliente: this.fb.control<number | null>(null, Validators.required),
    nombrepartner: ['', [Validators.required, Validators.minLength(3)]],
    contacto_tecnico_nombre: ['', Validators.required],
    contacto_tecnico_gmail: ['', [Validators.required, Validators.email]],
  });

  /** Clave por intento del usuario: se reutiliza si reintenta tras un fallo. */
  private claveRegistro = nuevaClaveIdempotencia();

  ngOnInit(): void {
    this.modo = (this.route.snapshot.data['modo'] as Modo) ?? 'ver';
    if (this.modo === 'ver') {
      this.cargar();
    } else {
      this.cargarClientesElegibles();
    }
  }

  /**
   * Sin esta carga el combobox queda vacío y el alta es inalcanzable. Solo se
   * ofrecen clientes ELEGIBLES, así que el usuario no puede provocar ni el 422
   * de «sin suscripción» ni el 409 de duplicado (BE-DELTA-03, FR-UI-004).
   */
  cargarClientesElegibles(): void {
    this.api.clientesElegibles().subscribe({
      next: (res) => this.clientes.set(res.data),
      error: () =>
        this.errorAccion.set(
          'No se pudo cargar la lista de clientes. Reintenta en unos segundos.',
        ),
    });
  }

  presentacion = presentacionDe;

  entorno(c: CredencialItem) {
    return presentacionEntorno(c.entorno);
  }

  vigencia(c: CredencialItem): string {
    return formatearVigencia(c.fecha_expiracion);
  }

  plan(p: PartnerDetalle): string {
    return formatearPlan(p.planapi);
  }

  cupoMes(p: PartnerDetalle): string {
    return formatearCupo(p.limitellamadasmes);
  }

  cupoMinuto(p: PartnerDetalle): string {
    return formatearCupo(p.limitellamadasminuto);
  }

  /**
   * Solo tiene sentido asignar plan si aún no lo tiene, y nunca sobre un
   * partner suspendido: toda acción de habilitación sobre él daría 409
   * (CA-PON-012, FR-UI-034).
   */
  puedeAsignarPlan(p: PartnerDetalle): boolean {
    return !estaSuspendido(p) && p.estado === 'Registrado';
  }

  suspendido = estaSuspendido;

  esAdministrador(): boolean {
    return this.authApi.hasRole('Administrador');
  }

  async suspender(p: PartnerDetalle): Promise<void> {
    const confirmado = await this.confirmDialog.confirm({
      title: 'Suspender acceso',
      message: `Se desactivarán TODAS las credenciales de ${p.nombrepartner}, de pruebas y de producción, y se le notificará el motivo.`,
      tone: 'danger',
      confirmLabel: 'Suspender',
      cancelLabel: 'Cancelar',
    });
    if (!confirmado) {
      return;
    }
    this.cambiandoAcceso.set(true);
    this.api
      .suspender(p.idpartner, 'Suspensión manual desde la consola', nuevaClaveIdempotencia())
      .subscribe({
        next: (res) => {
          this.cambiandoAcceso.set(false);
          this.mensajeAcceso.set(
            `Acceso suspendido. Credenciales desactivadas: ${res.data.credenciales_desactivadas}.`,
          );
          this.cargar();
        },
        error: () => {
          this.cambiandoAcceso.set(false);
          this.mensajeAcceso.set('No se pudo suspender el acceso.');
        },
      });
  }

  async reactivar(p: PartnerDetalle): Promise<void> {
    const confirmado = await this.confirmDialog.confirm({
      title: 'Reactivar acceso',
      message: `Se restituirán solo las credenciales que estaban activas antes de la suspensión de ${p.nombrepartner}.`,
      confirmLabel: 'Reactivar',
      cancelLabel: 'Cancelar',
    });
    if (!confirmado) {
      return;
    }
    this.cambiandoAcceso.set(true);
    this.api
      .reactivar(p.idpartner, 'Reactivación manual desde la consola', nuevaClaveIdempotencia())
      .subscribe({
        next: (res) => {
          this.cambiandoAcceso.set(false);
          const noRest = res.data.credenciales_no_restituidas;
          this.mensajeAcceso.set(
            `Acceso reactivado. Credenciales restituidas: ${res.data.credenciales_restituidas}` +
              (noRest ? `; ${noRest} siguen inactivas por haber sido revocadas.` : '.'),
          );
          this.cargar();
        },
        error: () => {
          this.cambiandoAcceso.set(false);
          this.mensajeAcceso.set('No se pudo reactivar el acceso.');
        },
      });
  }

  cargar(): void {
    const idpartner = Number(this.route.snapshot.paramMap.get('idpartner'));
    this.cargando.set(true);
    this.errorCarga.set(null);
    this.api.detalle(idpartner).subscribe({
      next: (res) => {
        this.partner.set(res.data);
        this.cargando.set(false);
      },
      error: () => {
        this.errorCarga.set('No se pudo cargar el detalle del partner.');
        this.cargando.set(false);
      },
    });
  }

  guardar(): void {
    if (this.form.invalid) {
      return;
    }
    this.guardando.set(true);
    this.errorAccion.set(null);
    this.idpartnerDuplicado.set(null);

    const v = this.form.getRawValue();
    this.api
      .registrar(
        {
          idcliente: Number(v.idcliente),
          nombrepartner: v.nombrepartner,
          contacto_tecnico_nombre: v.contacto_tecnico_nombre,
          contacto_tecnico_gmail: v.contacto_tecnico_gmail,
        },
        this.claveRegistro,
      )
      .subscribe({
        next: (res) => {
          this.guardando.set(false);
          void this.router.navigate(['/partners/consola', res.data.idpartner]);
        },
        error: (err) => {
          this.guardando.set(false);
          this.presentarError(err);
        },
      });
  }

  asignarPlan(p: PartnerDetalle): void {
    this.asignando.set(true);
    this.errorAccion.set(null);
    this.api.asignarPlan(p.idpartner, nuevaClaveIdempotencia()).subscribe({
      next: () => {
        this.asignando.set(false);
        this.cargar();
      },
      error: (err) => {
        this.asignando.set(false);
        this.presentarError(err);
      },
    });
  }

  /**
   * Cada fallo de negocio se presenta con su explicación accionable. El
   * duplicado además expone el `idpartner_existente` que devuelve el backend,
   * para poder navegar hasta él en vez de dejar al usuario buscándolo.
   */
  private presentarError(err: unknown): void {
    const cuerpo = (err as { error?: Record<string, unknown> })?.error ?? {};
    const code = String(cuerpo['code'] ?? '');

    if (code === 'partner_duplicado') {
      const existente = cuerpo['idpartner_existente'];
      this.idpartnerDuplicado.set(existente ? Number(existente) : null);
      this.errorAccion.set('Este cliente ya tiene un partner registrado.');
      return;
    }
    this.errorAccion.set(
      COPY_ERROR[code] ?? String(cuerpo['detail'] ?? 'No se pudo completar la operación.'),
    );
  }
}
