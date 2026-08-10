import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { timer } from 'rxjs';

import { TablerIconComponent } from '../../../../../shared/ui/icon/tabler-icon.component';
import { NotificationService } from '../../../../../shared/notifications/notification.service';
import { LIST_PAGE_SHELL_CLASS } from '../../../../../shared/ui/list-states/list-table.styles';
import { AuthApiService } from '../../../../cuentas-clientes/auth/services/auth-api.service';
import { CatalogoItem } from '../../../../accidentes/services/models/accidente.types';
import { UbicacionCatalogoApiService } from '../../../../accidentes/services/ubicacion-catalogo-api.service';
import { ListaSeleccionStorage } from '../../lista-seleccion.storage';
import { UnidadEmergenciaFacadeService } from '../../services/unidad-emergencia-facade.service';
import {
  TipoPropiedad,
  TipoUnidadEmergencia,
  UnidadCreateRequest,
  UnidadPatchRequest,
} from '../../models/unidad-emergencia.contract';

type FormMode = 'create' | 'edit';

interface UnidadFormState {
  idcondado: number | null;
  tipopropiedad: TipoPropiedad;
  placa: string;
  capacidad: string;
  contactoproveedor: string;
  unidademergencia: string;
  tipounidademergencia: TipoUnidadEmergencia;
  gmail: string;
  idcliente: number | null;
  idunidademergencia: number | null;
  latitud: number | null;
  longitud: number | null;
}

const FORM_VACIO: UnidadFormState = {
  idcondado: null,
  tipopropiedad: 'Externa',
  placa: '',
  capacidad: '',
  contactoproveedor: '',
  unidademergencia: '',
  tipounidademergencia: 'Ambulancia',
  gmail: '',
  idcliente: null,
  idunidademergencia: null,
  latitud: null,
  longitud: null,
};

@Component({
  selector: 'app-alta-unidades-formulario-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TablerIconComponent],
  template: `
    <div [class]="pageShellClass" data-testid="formulario-page">
      <a
        routerLink="/red-operativa/alta-unidades/catalogo"
        class="mb-2 inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-text-primary"
      >
        <app-tabler-icon name="arrow-left" [size]="16" />
        Volver al catálogo
      </a>

      <header class="mt-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 class="text-[28px] font-bold text-text-primary">
            {{ mode === 'create' ? 'Nueva unidad' : 'Editar unidad' }}
          </h1>
          @if (form.idunidademergencia && mode === 'edit') {
            <p class="mt-1 font-mono text-sm text-text-secondary">
              #{{ form.idunidademergencia }} · {{ form.placa }}
            </p>
          }
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            (click)="cancelar()"
            class="inline-flex h-11 items-center gap-2 rounded-md border border-border-default px-4 text-sm font-medium text-text-primary hover:bg-bg-page"
          >
            Cancelar
          </button>
          <button
            type="button"
            data-testid="btn-guardar"
            [disabled]="guardando || cargando"
            (click)="guardar()"
            class="inline-flex h-11 items-center gap-2 rounded-md bg-accent-primary px-4 text-sm font-semibold text-white hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-80"
          >
            @if (guardando) {
              Guardando…
            } @else {
              {{ mode === 'create' ? 'Guardar' : 'Guardar cambios' }}
            }
          </button>
        </div>
      </header>

      @if (cargando) {
        <p class="mt-6 text-sm text-text-secondary">Cargando unidad…</p>
      } @else {
        <form
          class="mt-6 grid grid-cols-1 gap-4 rounded-lg border border-border-default bg-bg-surface p-6 sm:grid-cols-2"
          (ngSubmit)="guardar()"
        >
          @if (mode === 'edit') {
            <div class="block sm:col-span-2">
              <span class="mb-1 block text-sm font-medium text-text-secondary">Dueño</span>
              <p class="text-sm text-text-primary">{{ duenioLabel }}</p>
            </div>
          }

          <div class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">País</span>
            <select
              #primerCampo
              [ngModel]="cascadaPais"
              (ngModelChange)="onPaisChange($event)"
              name="cascadaPais"
              data-testid="select-pais"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
            >
              <option [ngValue]="null">— Selecciona —</option>
              @for (p of paises; track p.id) {
                <option [ngValue]="p.id">{{ p.nombre }}</option>
              }
            </select>
          </div>

          <div class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Estado / región</span>
            <select
              [ngModel]="cascadaEstado"
              (ngModelChange)="onEstadoChange($event)"
              name="cascadaEstado"
              data-testid="select-estado"
              [disabled]="!cascadaPais"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <option [ngValue]="null">— Selecciona —</option>
              @for (e of estados; track e.id) {
                <option [ngValue]="e.id">{{ e.nombre }}</option>
              }
            </select>
          </div>

          <div class="block sm:col-span-2">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Condado</span>
            <select
              [ngModel]="form.idcondado"
              (ngModelChange)="onCondadoChange($event)"
              name="idcondado"
              data-testid="select-condado"
              required
              [disabled]="!cascadaEstado"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <option [ngValue]="null">— Selecciona —</option>
              @for (c of condados; track c.id) {
                <option [ngValue]="c.id">{{ c.nombre }}</option>
              }
            </select>
          </div>

          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Tipo de propiedad</span>
            <select
              [(ngModel)]="form.tipopropiedad"
              name="tipopropiedad"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none"
            >
              <option value="Propia">Propia</option>
              <option value="Externa">Externa</option>
            </select>
          </label>

          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Placa</span>
            <input
              [(ngModel)]="form.placa"
              name="placa"
              [disabled]="mode === 'edit'"
              required
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 font-mono text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15 disabled:bg-bg-page disabled:opacity-80"
            />
          </label>

          <label class="block">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Capacidad</span>
            <input
              [(ngModel)]="form.capacidad"
              name="capacidad"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
            />
          </label>

          @if (form.tipopropiedad === 'Externa') {
            <label class="block sm:col-span-2">
              <span class="mb-1 block text-sm font-medium text-text-secondary">Contacto proveedor</span>
              <input
                [(ngModel)]="form.contactoproveedor"
                name="contactoproveedor"
                class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
              />
            </label>
          }

          <label class="block sm:col-span-2">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Nombre de la unidad</span>
            <input
              [(ngModel)]="form.unidademergencia"
              name="unidademergencia"
              required
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
            />
          </label>

          <label class="block sm:col-span-2">
            <span class="mb-1 block text-sm font-medium text-text-secondary">Tipo de unidad</span>
            <select
              [(ngModel)]="form.tipounidademergencia"
              name="tipounidademergencia"
              class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none"
            >
              <option value="Ambulancia">Ambulancia</option>
              <option value="Grúa">Grúa</option>
              <option value="Patrulla">Patrulla</option>
              <option value="Bomberos">Bomberos</option>
              <option value="Defensa Civil">Defensa Civil</option>
            </select>
          </label>

          @if (mode === 'create') {
            <label class="block sm:col-span-2">
              <span class="mb-1 block text-sm font-medium text-text-secondary">
                Gmail unidad (opcional — sin él, la unidad no podrá declarar disponibilidad hasta
                que se le asigne login)
              </span>
              <input
                type="email"
                [(ngModel)]="form.gmail"
                name="gmail"
                data-testid="input-gmail"
                class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
              />
            </label>
          }

          @if (mode === 'edit') {
            <label class="block">
              <span class="mb-1 block text-sm font-medium text-text-secondary">Latitud</span>
              <input
                type="number"
                step="any"
                [(ngModel)]="form.latitud"
                name="latitud"
                class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
              />
            </label>
            <label class="block">
              <span class="mb-1 block text-sm font-medium text-text-secondary">Longitud</span>
              <input
                type="number"
                step="any"
                [(ngModel)]="form.longitud"
                name="longitud"
                class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:border-accent-primary focus:outline-none focus:ring-4 focus:ring-accent-primary/15"
              />
            </label>
          }
        </form>

        @if (requiereConfirmacionCritica) {
          <div
            role="alert"
            class="mt-4 space-y-3 rounded-md border-l-4 border-alert-warning bg-alert-warning-bg px-4 py-3 text-sm text-alert-warning"
          >
            <div class="flex items-center gap-2">
              <app-tabler-icon name="alert-triangle" [size]="18" />
              <span>La unidad tiene un despacho activo. Confirma para aplicar el cambio crítico.</span>
            </div>
            <button
              type="button"
              (click)="guardar(true)"
              class="rounded-md border border-alert-warning px-4 py-2 text-sm font-medium text-alert-warning hover:bg-alert-warning/10"
            >
              Confirmar edición crítica
            </button>
          </div>
        }

        @if (invitacionPendiente && form.idunidademergencia) {
          <div
            role="alert"
            class="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-md border-l-4 border-alert-warning bg-alert-warning-bg px-4 py-3 text-sm text-alert-warning"
            data-testid="invitacion-error-banner"
          >
            <span>{{ invitacionErrorMsg }}</span>
            <button
              type="button"
              data-testid="btn-reenviar-invitacion"
              [disabled]="reenviando"
              (click)="reenviarInvitacion()"
              class="rounded-md border border-alert-warning px-4 py-2 text-sm font-medium hover:bg-alert-warning/10 disabled:opacity-50"
            >
              {{ reenviando ? 'Reenviando…' : 'Reenviar' }}
            </button>
          </div>
        }

        @if (errorMensaje) {
          <div
            role="alert"
            class="mt-4 flex items-center gap-2 rounded-md border-l-4 border-alert-critical bg-alert-critical-bg px-4 py-3 text-sm text-alert-critical"
          >
            <app-tabler-icon name="alert-triangle" [size]="18" />
            <span>{{ errorMensaje }}</span>
          </div>
        }
      }
    </div>
  `,
})
export class FormularioPage implements OnInit, AfterViewInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly facade = inject(UnidadEmergenciaFacadeService);
  private readonly notifications = inject(NotificationService);
  private readonly listaSeleccion = inject(ListaSeleccionStorage);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly ubicacionCatalogo = inject(UbicacionCatalogoApiService);
  private readonly auth = inject(AuthApiService);

  @ViewChild('primerCampo') private primerCampo?: ElementRef<HTMLSelectElement>;

  readonly pageShellClass = LIST_PAGE_SHELL_CLASS;

  mode: FormMode = 'create';
  form: UnidadFormState = { ...FORM_VACIO };
  cargando = false;
  guardando = false;
  reenviando = false;
  errorMensaje: string | null = null;
  requiereConfirmacionCritica = false;
  invitacionPendiente = false;
  invitacionErrorMsg = '';
  duenioLabel = 'Cuenta de tu sesión';

  // Cascada País → Estado/Región → Condado (solo UX de selección; el payload
  // sigue enviando idcondado, sin cambios de contrato con el backend).
  cascadaPais: number | null = null;
  cascadaEstado: number | null = null;
  paises: CatalogoItem[] = [];
  estados: CatalogoItem[] = [];
  condados: CatalogoItem[] = [];

  ngOnInit(): void {
    const dataMode = this.route.snapshot.data['mode'] as FormMode | undefined;
    const idParam = this.route.snapshot.paramMap.get('idunidademergencia');
    this.mode = dataMode === 'edit' || idParam ? 'edit' : 'create';

    if (this.mode === 'create') {
      this.form = { ...FORM_VACIO };
      this.cargarPaises();
      return;
    }

    const id = Number(idParam);
    if (!Number.isFinite(id) || id <= 0) {
      this.errorMensaje = 'Identificador de unidad inválido.';
      return;
    }
    this.listaSeleccion.set(String(id));
    this.cargando = true;
    this.cdr.markForCheck();
    this.facade.obtener(id).subscribe((result) => {
      this.cargando = false;
      if (result.ok && result.data) {
        const u = result.data;
        this.form = {
          idcondado: u.idcondado,
          tipopropiedad: u.tipopropiedad,
          placa: u.placa,
          capacidad: u.capacidad ?? '',
          contactoproveedor: u.contactoproveedor ?? '',
          unidademergencia: u.unidademergencia,
          tipounidademergencia: u.tipounidademergencia,
          gmail: '',
          idcliente: u.idcliente,
          idunidademergencia: u.idunidademergencia,
          latitud: u.latitud,
          longitud: u.longitud,
        };
        this.duenioLabel = this.auth.getProfile()?.gmail ?? 'Cuenta de tu sesión';
        this.resolverCascadaPorCondado(u.idcondado);
        queueMicrotask(() => this.focusPrimerCampo());
      } else {
        this.errorMensaje = result.error ?? 'No se pudo cargar la unidad';
      }
      this.cdr.markForCheck();
    });
  }

  ngAfterViewInit(): void {
    this.focusPrimerCampo();
  }

  cancelar(): void {
    void this.router.navigate(['/red-operativa/alta-unidades/catalogo']);
  }

  onPaisChange(idpais: number | null): void {
    this.cascadaPais = idpais;
    this.cascadaEstado = null;
    this.estados = [];
    this.condados = [];
    this.form.idcondado = null;
    if (idpais) {
      this.ubicacionCatalogo.listarEstados(idpais).subscribe((estados) => {
        this.estados = estados;
        this.cdr.markForCheck();
      });
    }
  }

  onEstadoChange(idestado: number | null): void {
    this.cascadaEstado = idestado;
    this.condados = [];
    this.form.idcondado = null;
    if (idestado) {
      this.ubicacionCatalogo.listarCondados(idestado).subscribe((condados) => {
        this.condados = condados;
        this.cdr.markForCheck();
      });
    }
  }

  onCondadoChange(idcondado: number | null): void {
    this.form.idcondado = idcondado;
  }

  private cargarPaises(): void {
    this.ubicacionCatalogo.listarPaises().subscribe({
      next: (paises) => {
        this.paises = paises;
        this.cdr.markForCheck();
      },
      error: () => {
        this.paises = [];
      },
    });
  }

  /**
   * Resuelve país/estado a los que pertenece un idcondado ya asignado (modo edición),
   * para pre-seleccionar la cascada en vez de mostrar solo el ID crudo.
   * Recorre país→estados→condados buscando coincidencia (catálogo geográfico acotado).
   */
  private resolverCascadaPorCondado(idcondado: number): void {
    this.ubicacionCatalogo.listarPaises().subscribe((paises) => {
      this.paises = paises;
      for (const pais of paises) {
        this.ubicacionCatalogo.listarEstados(pais.id).subscribe((estados) => {
          for (const estado of estados) {
            this.ubicacionCatalogo.listarCondados(estado.id).subscribe((condados) => {
              const match = condados.find((c) => c.id === idcondado);
              if (match) {
                this.cascadaPais = pais.id;
                this.cascadaEstado = estado.id;
                this.estados = estados;
                this.condados = condados;
                this.cdr.markForCheck();
              }
            });
          }
        });
      }
    });
  }

  guardar(confirmarEdicionCritica = false): void {
    if (this.guardando) return;
    this.errorMensaje = null;
    this.requiereConfirmacionCritica = false;

    if (this.mode === 'create') {
      this.guardarAlta();
      return;
    }
    this.guardarEdicion(confirmarEdicionCritica);
  }

  reenviarInvitacion(): void {
    if (!this.form.idunidademergencia || this.reenviando) return;
    this.reenviando = true;
    this.facade.reenviarInvitacion(this.form.idunidademergencia).subscribe((result) => {
      this.reenviando = false;
      if (result.ok && result.data?.invitacion_enviada) {
        this.invitacionPendiente = false;
        this.notifications.toast('Invitación reenviada correctamente.', 'success');
        this.irCatalogoTrasAlta();
      } else {
        this.invitacionErrorMsg =
          result.data?.invitacion_error ??
          result.error ??
          'No se pudo reenviar la invitación.';
        this.notifications.toast(this.invitacionErrorMsg, 'critical');
      }
    });
  }

  private guardarAlta(): void {
    if (!this.form.idcondado || !this.form.placa.trim() || !this.form.unidademergencia.trim()) {
      this.errorMensaje = 'Completa los campos requeridos (condado, placa y nombre).';
      return;
    }

    const body: UnidadCreateRequest = {
      idcondado: this.form.idcondado,
      tipopropiedad: this.form.tipopropiedad,
      placa: this.form.placa.trim(),
      capacidad: this.form.capacidad.trim() || undefined,
      contactoproveedor: this.form.contactoproveedor.trim() || undefined,
      unidademergencia: this.form.unidademergencia.trim(),
      tipounidademergencia: this.form.tipounidademergencia,
      gmail: this.form.gmail.trim() || undefined,
    };

    this.guardando = true;
    this.facade.registrar(body).subscribe((result) => {
      this.guardando = false;
      if (!result.ok || !result.data) {
        this.errorMensaje = this.humanizarError(result.error);
        this.notifications.toast(this.errorMensaje, 'critical');
        return;
      }

      const created = result.data;
      this.form.idunidademergencia = created.idunidademergencia;
      this.listaSeleccion.set(String(created.idunidademergencia));

      if (created.invitacion_enviada) {
        this.notifications.toast(
          `Unidad #${created.idunidademergencia} (${created.placa}) registrada. Invitación enviada.`,
          'success',
        );
      } else {
        this.invitacionPendiente = true;
        this.invitacionErrorMsg =
          created.invitacion_error ??
          'Unidad creada, pero no se pudo enviar la invitación. Use Reenviar.';
        this.notifications.toast(this.invitacionErrorMsg, 'warning');
      }
      // Siempre volver al catálogo (con poll Pinot) para que la unidad se vea listada.
      this.irCatalogoTrasAlta();
    });
  }

  private guardarEdicion(confirmarEdicionCritica: boolean): void {
    if (this.form.idunidademergencia == null) return;

    const body: UnidadPatchRequest = {
      tipopropiedad: this.form.tipopropiedad,
      capacidad: this.form.capacidad.trim() || undefined,
      idcondado: this.form.idcondado ?? undefined,
      contactoproveedor: this.form.contactoproveedor.trim() || undefined,
      unidademergencia: this.form.unidademergencia.trim(),
      tipounidademergencia: this.form.tipounidademergencia,
      latitud: this.form.latitud ?? undefined,
      longitud: this.form.longitud ?? undefined,
    };

    this.guardando = true;
    this.facade.editar(this.form.idunidademergencia, body, confirmarEdicionCritica).subscribe((result) => {
      this.guardando = false;
      if (result.ok) {
        this.listaSeleccion.set(String(this.form.idunidademergencia));
        this.notifications.toast('Unidad actualizada correctamente.', 'success');
        void this.router.navigate(['/red-operativa/alta-unidades/catalogo']);
      } else if (result.error?.toLowerCase().includes('despacho activo')) {
        this.requiereConfirmacionCritica = true;
      } else {
        this.errorMensaje = this.humanizarError(result.error);
      }
    });
  }

  private irCatalogoTrasAlta(): void {
    const placa = this.form.placa.trim();
    // Poll breve para lag Kafka→Pinot; catálogo recarga con cursor=null (opcional q=placa).
    timer(1200).subscribe({
      next: () =>
        void this.router.navigate(['/red-operativa/alta-unidades/catalogo'], {
          queryParams: placa ? { q: placa } : {},
        }),
      error: () => void this.router.navigate(['/red-operativa/alta-unidades/catalogo']),
    });
  }

  private humanizarError(error: string | undefined): string {
    const raw = (error ?? 'No se pudo guardar la unidad.').trim();
    if (/correo ya registrado|gmail/i.test(raw)) {
      return `${raw} Usa un gmail distinto.`;
    }
    if (/ya existe una unidad activa con placa|placa/i.test(raw)) {
      return `${raw} Usa otra placa o da de baja/reactiva la existente.`;
    }
    return raw;
  }

  private focusPrimerCampo(): void {
    this.primerCampo?.nativeElement?.focus();
  }
}
