import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { ConfirmDialogService } from '../../../../shared/notifications/confirm-dialog.service';

import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { ListErrorStateComponent } from '../../../../shared/ui/list-states/list-error-state.component';
import { ListLoadingSkeletonComponent } from '../../../../shared/ui/list-states/list-loading-skeleton.component';
import { LIST_PAGE_SHELL_CLASS } from '../../../../shared/ui/list-states/list-table.styles';
import { ENTORNOS, presentacionEntorno } from '../../entorno.constants';
import { ESTADO_SUSPENDIDO, presentacionDe } from '../../estado-partner.constants';
import {
  PartnerApiService,
  nuevaClaveIdempotencia,
} from '../../services/partner-api.service';
import {
  estaVencida,
  formatearCupo,
  formatearPlan,
  formatearVigencia,
} from '../../services/models/centinelas';
import type {
  CredencialItem,
  Entorno,
  EstadoAcceso,
  PartnerDetalle,
} from '../../services/models/partner.types';
import { ESTADO_CREDENCIAL_EMITIDA } from '../secreto-emitido/secreto-emitido.page';

const COPY_ERROR: Record<string, string> = {
  sin_plan:
    'Tu plan de acceso aún no está asignado. Un administrador debe asignarlo antes de que puedas emitir credenciales.',
  nombre_duplicado: 'Ya tienes una credencial activa con ese nombre en este entorno.',
  partner_suspendido: 'Tu acceso está suspendido. Contacta al administrador.',
  ruta_invalida:
    'Debes tener una credencial de pruebas activa antes de solicitar el paso a producción.',
};

/** Devuelve el control al usuario si el backend no responde (design-system § 5). */
const TIMEOUT_ACCION_MS = 15_000;

/**
 * Portal del partner — su estado, su cupo y sus credenciales.
 *
 * El primer requisito de toda la pantalla es resolver **cuál es su partner**:
 * el token de sesión solo lleva `idusuario`, así que sin `GET /partners/me`
 * (BE-DELTA-01) no hay nada que mostrar.
 *
 * Las credenciales se agrupan **bajo encabezados por entorno** y no en una
 * tabla plana con una columna «Entorno»: confundir pruebas con producción al
 * rotar sería un error caro, y una separación estructural se escanea mejor que
 * una columna (RN-PON-008, FR-UI-016).
 */
@Component({
  selector: 'app-mi-integracion',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    TablerIconComponent,
    ListErrorStateComponent,
    ListLoadingSkeletonComponent,
    DatePipe,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section [class]="shellClass">
      <h1 class="m-0 text-2xl font-bold text-text-primary">Mi integración</h1>

      @if (cargando()) {
        <app-list-loading-skeleton [count]="4" />
      } @else if (errorCarga()) {
        <app-list-error-state [message]="errorCarga()!" (retry)="cargar()" />
      } @else {
        <!-- El alias "as" solo se admite en el @if primario, no en un @else if -->
        @if (partner(); as p) {
        <!-- Estado + qué sigue: un estado sin siguiente paso deja al partner
             sin saber qué hacer (FR-UI-015). -->
        <div class="mt-4 rounded-lg border border-border-default bg-bg-surface p-6">
          <span
            class="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium"
            [class]="presentacion(p.estado).tono"
            data-testid="badge-estado"
          >
            <app-tabler-icon [name]="presentacion(p.estado).icono" [size]="14" />
            {{ p.estado }}
          </span>
          <p class="mt-3 text-sm text-text-secondary" data-testid="que-sigue">
            {{ presentacion(p.estado).siguiente }}
          </p>
        </div>

        <!-- RN-PAC-016: el partner suspendido conserva el acceso de lectura, y
             esta es justo la pantalla donde entiende POR QUÉ se le cortó y qué
             tiene que hacer. Decirle solo "contacta al administrador" lo deja
             sin la información que el backend ya tiene. -->
        @if (acceso(); as a) {
          @if (!a.activo) {
            <div
              class="mt-4 rounded-lg border border-alert-critical bg-alert-critical-bg p-6"
              data-testid="panel-suspension"
            >
              <h2 class="m-0 mb-2 flex items-center gap-2 text-lg font-semibold text-alert-critical">
                <app-tabler-icon name="ban" [size]="18" />
                Por qué está suspendido tu acceso
              </h2>
              <p class="m-0 text-sm text-text-primary" data-testid="motivo-suspension">
                {{ a.motivo_suspension || 'Sin motivo registrado.' }}
              </p>
              @if (a.fecha_suspension) {
                <p class="m-0 mt-1 text-sm text-text-secondary">
                  <!-- Fecha legible, no el ISO crudo del backend (F4/F6). -->
                  Suspendido desde {{ a.fecha_suspension | date: 'dd/MM/yyyy HH:mm' }}.
                </p>
              }
              @if (a.en_mora) {
                <p class="m-0 mt-1 text-sm text-text-secondary" data-testid="dias-mora">
                  Llevas {{ a.dias_mora }} día(s) de mora. Regularizar el pago es lo que permite
                  volver a operar; la reactivación la confirma un administrador.
                </p>
              }
              <p class="m-0 mt-3 text-sm text-text-secondary">
                Tus credenciales están desactivadas mientras dure la suspensión. Puedes seguir
                consultando esta pantalla y tu consumo.
              </p>
              @if (a.historial.length) {
                <details class="mt-3 text-sm">
                  <summary class="cursor-pointer text-text-secondary">
                    Historial de acceso ({{ a.historial.length }})
                  </summary>
                  <ul class="mt-2 grid gap-1">
                    @for (h of a.historial; track h.fecha) {
                      <li class="text-text-secondary">
                        {{ h.fecha | date: 'dd/MM/yyyy HH:mm' }} — {{ h.tipo_cambio }}
                        @if (h.motivo) {
                          · {{ h.motivo }}
                        }
                      </li>
                    }
                  </ul>
                </details>
              }
            </div>
          }
        }

        <div class="mt-4 rounded-lg border border-border-default bg-bg-surface p-6">
          <h2 class="m-0 mb-4 text-lg font-semibold text-text-primary">Plan y cupo</h2>
          <dl class="grid grid-cols-[auto_1fr] gap-x-6 gap-y-3 text-sm">
            <dt class="text-xs uppercase tracking-wide text-text-secondary">Plan</dt>
            <dd class="m-0 text-text-primary" data-testid="dd-plan">{{ plan(p) }}</dd>
            <dt class="text-xs uppercase tracking-wide text-text-secondary">Llamadas / mes</dt>
            <dd class="m-0 text-text-primary">{{ cupoMes(p) }}</dd>
            <dt class="text-xs uppercase tracking-wide text-text-secondary">Llamadas / minuto</dt>
            <dd class="m-0 text-text-primary">{{ cupoMinuto(p) }}</dd>
          </dl>
        </div>

        @if (errorAccion()) {
          <div
            class="mt-4 rounded-lg border border-alert-critical bg-alert-critical-bg p-4 text-sm text-alert-critical"
            data-testid="banner-error"
            role="alert"
          >
            {{ errorAccion() }}
          </div>
        }

        <!-- Credenciales agrupadas POR ENTORNO -->
        @for (e of entornos; track e) {
          @if (mostrarGrupo(e)) {
            <section
              class="mt-4 rounded-lg border border-border-default bg-bg-surface p-6"
              [attr.data-testid]="'grupo-' + e"
            >
              <header class="mb-1 flex flex-wrap items-center gap-2">
                <span
                  class="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium"
                  [class]="entornoDe(e).tono"
                >
                  <app-tabler-icon [name]="entornoDe(e).icono" [size]="14" />
                  {{ entornoDe(e).etiqueta }}
                </span>
              </header>
              <p class="m-0 mb-4 text-xs text-text-secondary">{{ entornoDe(e).notaVigencia }}</p>

              @if (credencialesDe(e).length === 0) {
                <p class="m-0 text-sm text-text-secondary">
                  Aún no has emitido ninguna credencial en este entorno.
                </p>
              } @else {
                <ul class="grid gap-2">
                  @for (c of credencialesDe(e); track c.idcredencial) {
                    <li
                      class="flex flex-wrap items-center gap-3 rounded-md border border-border-default p-3 text-sm"
                      [attr.data-testid]="'credencial-' + c.idcredencial"
                    >
                      <span class="font-medium text-text-primary">{{ c.nombre_credencial }}</span>
                      @if (vencida(c)) {
                        <span
                          class="rounded-md bg-alert-media-bg px-2 py-0.5 text-xs font-medium text-alert-media"
                          [attr.data-testid]="'vencida-' + c.idcredencial"
                        >
                          Vencida
                        </span>
                        <button
                          type="button"
                          [attr.data-testid]="'btn-regenerar-' + c.idcredencial"
                          class="rounded-md border border-accent-primary px-3 py-1.5 text-xs font-medium text-accent-primary"
                          [disabled]="emitiendo()"
                          (click)="regenerar(c)"
                        >
                          Regenerar
                        </button>
                      } @else {
                        <span class="text-text-secondary" [attr.data-testid]="'vigencia-' + c.idcredencial">
                          {{ vigencia(c) }}
                        </span>
                        <!-- SRS §3.4.3: la revocación es autoservicio porque es
                             la reacción a un incidente de seguridad; "esperar
                             autorización sería el peor comportamiento posible".
                             El endpoint existía y ninguna pantalla lo llamaba. -->
                        <button
                          type="button"
                          [attr.data-testid]="'btn-revocar-' + c.idcredencial"
                          class="ml-auto rounded-md border border-alert-critical px-3 py-1.5 text-xs font-medium text-alert-critical hover:bg-alert-critical-bg disabled:opacity-50"
                          [disabled]="revocando() === c.idcredencial"
                          (click)="revocar(c)"
                        >
                          @if (revocando() === c.idcredencial) {
                            Revocando…
                          } @else {
                            Revocar
                          }
                        </button>
                      }
                    </li>
                  }
                </ul>
              }

              @if (puedeEmitirEn(e)) {
                <form [formGroup]="form" (ngSubmit)="emitir(e)" class="mt-4 grid gap-2 sm:flex sm:items-end">
                  <div class="grow">
                    <label class="mb-1 block text-sm font-medium text-text-secondary" [attr.for]="'nombre-' + e">
                      Nombre de la credencial
                    </label>
                    <input
                      [id]="'nombre-' + e"
                      [attr.data-testid]="'input-nombre-' + e"
                      [class]="inputClass"
                      formControlName="nombre_credencial"
                      placeholder="p. ej. plataforma-siniestros"
                    />
                    @if (nombreDuplicado(e)) {
                      <p class="mt-1 text-xs text-alert-critical" [attr.data-testid]="'error-nombre-' + e">
                        Ya tienes una credencial activa con ese nombre en este entorno.
                      </p>
                    }
                  </div>
                  <button
                    type="submit"
                    [attr.data-testid]="'btn-emitir-' + e"
                    class="rounded-lg bg-accent-primary px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
                    [disabled]="form.invalid || nombreDuplicado(e) || emitiendo()"
                  >
                    {{ emitiendo() ? 'Emitiendo…' : 'Emitir credencial' }}
                  </button>
                </form>
              } @else if (e === 'Sandbox' && sinPlan()) {
                <p class="mt-4 text-sm text-text-secondary" data-testid="copy-sin-plan">
                  Tu plan de acceso aún no está asignado. Un administrador debe asignarlo antes de
                  que puedas emitir credenciales.
                </p>
              }
            </section>
          }
        }

        <!-- Solicitar producción: solo desde «Pruebas activo» (FR-UI-026) -->
        <section class="mt-4 rounded-lg border border-border-default bg-bg-surface p-6">
          <h2 class="m-0 mb-3 text-lg font-semibold text-text-primary">Paso a producción</h2>
          @if (p.estado === 'Pruebas activo') {
            <form [formGroup]="formProduccion" (ngSubmit)="solicitarProduccion()" class="grid gap-2 sm:flex sm:items-end">
              <div class="grow">
                <label class="mb-1 block text-sm font-medium text-text-secondary" for="nombre-prod">
                  Nombre de la credencial de producción
                </label>
                <input
                  id="nombre-prod"
                  data-testid="input-nombre-produccion"
                  [class]="inputClass"
                  formControlName="nombre_credencial"
                />
              </div>
              <button
                type="submit"
                data-testid="btn-solicitar-produccion"
                class="rounded-lg bg-accent-primary px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
                [disabled]="formProduccion.invalid || solicitando()"
              >
                {{ solicitando() ? 'Solicitando…' : 'Solicitar paso a producción' }}
              </button>
            </form>
          } @else {
            <p class="m-0 text-sm text-text-secondary" data-testid="ruta-produccion">
              {{ presentacion(p.estado).siguiente }}
            </p>
          }
        </section>
        }
      }
    </section>
  `,
})
export class MiIntegracionPage implements OnInit {
  private readonly api = inject(PartnerApiService);
  private readonly router = inject(Router);
  private readonly confirmDialog = inject(ConfirmDialogService);
  private readonly fb = inject(FormBuilder);

  readonly partner = signal<PartnerDetalle | null>(null);
  readonly cargando = signal(true);
  readonly emitiendo = signal(false);
  /** idcredencial en curso de revocación, o null. */
  readonly revocando = signal<number | null>(null);
  /** Detalle de acceso; solo se carga si el partner está suspendido (RN-PAC-016). */
  readonly acceso = signal<EstadoAcceso | null>(null);
  readonly solicitando = signal(false);
  readonly errorCarga = signal<string | null>(null);
  readonly errorAccion = signal<string | null>(null);

  readonly entornos = ENTORNOS;
  readonly shellClass = LIST_PAGE_SHELL_CLASS;
  readonly inputClass =
    'w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary';

  readonly form = this.fb.nonNullable.group({
    nombre_credencial: ['', [Validators.required, Validators.minLength(3)]],
  });
  readonly formProduccion = this.fb.nonNullable.group({
    nombre_credencial: ['', [Validators.required, Validators.minLength(3)]],
  });

  /** Sin plan asignado, el centinela es `''` y no puede emitir (CA-PON-007). */
  readonly sinPlan = computed(() => !this.partner()?.planapi);

  /** Clave por intento del usuario; se reutiliza al reintentar tras un fallo. */
  private claveEmision = nuevaClaveIdempotencia();

  ngOnInit(): void {
    this.cargar();
  }

  presentacion = presentacionDe;
  entornoDe = presentacionEntorno;

  plan(p: PartnerDetalle): string {
    return formatearPlan(p.planapi);
  }

  cupoMes(p: PartnerDetalle): string {
    return formatearCupo(p.limitellamadasmes);
  }

  cupoMinuto(p: PartnerDetalle): string {
    return formatearCupo(p.limitellamadasminuto);
  }

  vigencia(c: CredencialItem): string {
    return formatearVigencia(c.fecha_expiracion);
  }

  vencida(c: CredencialItem): boolean {
    return estaVencida(c);
  }

  credencialesDe(entorno: Entorno): CredencialItem[] {
    return (this.partner()?.credenciales ?? []).filter((c) => c.entorno === entorno && c.activo);
  }

  /**
   * El grupo de producción no se muestra si el partner nunca fue promovido: un
   * bloque vacío sugeriría que le falta algo que aún no le corresponde.
   */
  mostrarGrupo(entorno: Entorno): boolean {
    if (entorno === 'Sandbox') {
      return true;
    }
    return this.partner()?.estado === 'Producción activa';
  }

  /** Producción solo tras la aprobación (BE-DELTA-02, FR-UI-027). */
  puedeEmitirEn(entorno: Entorno): boolean {
    const p = this.partner();
    if (!p || !p.activo || this.sinPlan()) {
      return false;
    }
    return entorno === 'Sandbox' || p.estado === 'Producción activa';
  }

  /** Validación en cliente: el 409 del backend no debería llegar a ocurrir. */
  nombreDuplicado(entorno: Entorno): boolean {
    const nombre = this.form.getRawValue().nombre_credencial.trim();
    if (!nombre) {
      return false;
    }
    return this.credencialesDe(entorno).some((c) => c.nombre_credencial === nombre);
  }

  cargar(): void {
    this.cargando.set(true);
    this.errorCarga.set(null);
    this.api.miPartner().subscribe({
      next: (res) => {
        this.partner.set(res.data);
        this.cargando.set(false);
        // Solo se pide cuando hace falta explicar una suspensión: en el resto
        // de estados no aporta nada y sería una llamada de más.
        if (res.data.estado === ESTADO_SUSPENDIDO) {
          this.api.estadoAcceso(res.data.idpartner).subscribe({
            next: (estado) => this.acceso.set(estado.data),
            // Si falla, la pantalla sigue siendo útil: el badge ya dice que
            // está suspendido; solo se pierde el detalle del motivo.
            error: () => this.acceso.set(null),
          });
        }
      },
      error: (err) => {
        const code = String((err as { error?: { code?: string } })?.error?.code ?? '');
        this.errorCarga.set(
          code === 'sin_partner' || code === 'sin_cliente'
            ? 'Tu usuario aún no tiene un perfil de partner asociado. Contacta al administrador.'
            : 'No se pudo cargar tu integración.',
        );
        this.cargando.set(false);
      },
    });
  }

  emitir(entorno: Entorno): void {
    if (this.form.invalid || this.nombreDuplicado(entorno)) {
      return;
    }
    this.ejecutarEmision(this.form.getRawValue().nombre_credencial.trim(), entorno);
  }

  /**
   * SRS §3.4.3 — revocación de autoservicio con reemplazo inmediato. La
   * credencial comprometida se corta y el partner recibe otra del mismo entorno
   * y nombre; las demás siguen operando sin interrupción.
   */
  async revocar(c: CredencialItem): Promise<void> {
    const confirmado = await this.confirmDialog.confirm({
      title: 'Revocar credencial',
      message: `Se invalidará «${c.nombre_credencial}» de inmediato y recibirás una de reemplazo con el mismo nombre. Tus otras credenciales seguirán funcionando.`,
      tone: 'danger',
      confirmLabel: 'Revocar',
      cancelLabel: 'Cancelar',
    });
    if (!confirmado) {
      return;
    }
    this.revocando.set(c.idcredencial);
    this.errorAccion.set(null);
    this.api
      .revocarCredencial(c.idcredencial, 'Revocada por el partner', nuevaClaveIdempotencia())
      .subscribe({
        next: (res) => {
          this.revocando.set(null);
          // El secreto del reemplazo viaja una sola vez: se entrega en la misma
          // pantalla que usa la emisión, no se pierde en un toast.
          void this.router.navigate(['/partners/portal/credencial-emitida'], {
            state: { [ESTADO_CREDENCIAL_EMITIDA]: res.data.reemplazo },
          });
        },
        error: (err) => {
          this.revocando.set(null);
          this.errorAccion.set(
            this.detalleError(err) ?? 'No se pudo revocar la credencial.',
          );
        },
      });
  }

  /** Detalle accionable que devuelve el backend, si lo hay. */
  private detalleError(err: unknown): string | null {
    const cuerpo = (err as { error?: { detail?: unknown } } | undefined)?.error;
    const detalle = cuerpo?.detail;
    return typeof detalle === 'string' && detalle.trim() ? detalle : null;
  }

  /** Regenerar reutiliza el flujo de emisión: mismo nombre, credencial nueva. */
  regenerar(c: CredencialItem): void {
    this.claveEmision = nuevaClaveIdempotencia();
    this.ejecutarEmision(c.nombre_credencial, c.entorno);
  }

  solicitarProduccion(): void {
    if (this.formProduccion.invalid) {
      return;
    }
    this.solicitando.set(true);
    this.errorAccion.set(null);
    const devolverControl = setTimeout(() => this.solicitando.set(false), TIMEOUT_ACCION_MS);

    this.api
      .solicitarProduccion(
        this.partner()!.idpartner,
        this.formProduccion.getRawValue().nombre_credencial.trim(),
        nuevaClaveIdempotencia(),
      )
      .subscribe({
        next: () => {
          clearTimeout(devolverControl);
          this.solicitando.set(false);
          this.formProduccion.reset();
          this.cargar();
        },
        error: (err) => {
          clearTimeout(devolverControl);
          this.solicitando.set(false);
          this.presentarError(err);
        },
      });
  }

  private ejecutarEmision(nombre: string, entorno: Entorno): void {
    this.emitiendo.set(true);
    this.errorAccion.set(null);
    // Si el backend no responde, el botón vuelve a su estado normal en vez de
    // quedarse cargando indefinidamente (design-system § 5).
    const devolverControl = setTimeout(() => this.emitiendo.set(false), TIMEOUT_ACCION_MS);

    this.api
      .emitirCredencial(
        this.partner()!.idpartner,
        { nombre_credencial: nombre, entorno },
        this.claveEmision,
      )
      .subscribe({
        next: (res) => {
          clearTimeout(devolverControl);
          this.emitiendo.set(false);
          this.form.reset();
          // Intento consumido: el siguiente es una intención distinta.
          this.claveEmision = nuevaClaveIdempotencia();
          // El secreto viaja en memoria, jamás por la URL.
          void this.router.navigate(['/partners/portal/credencial-emitida'], {
            state: { [ESTADO_CREDENCIAL_EMITIDA]: res.data },
          });
        },
        error: (err) => {
          clearTimeout(devolverControl);
          this.emitiendo.set(false);
          // La clave NO se renueva: un reintento del mismo intento debe
          // recuperar el mismo secreto en vez de emitir otra credencial.
          this.presentarError(err);
        },
      });
  }

  private presentarError(err: unknown): void {
    const cuerpo = (err as { error?: Record<string, unknown> })?.error ?? {};
    const code = String(cuerpo['code'] ?? '');
    this.errorAccion.set(
      COPY_ERROR[code] ?? String(cuerpo['detail'] ?? 'No se pudo completar la operación.'),
    );
  }
}
