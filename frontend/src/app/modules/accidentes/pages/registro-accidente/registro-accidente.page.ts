import { DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  FormBuilder,
  FormsModule,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import { debounceTime, finalize } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { LatLng, LocationPickerMapComponent } from '../../../../shared/ui/map/location-picker-map.component';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AccidenteApiService } from '../../services/accidente-api.service';
import { GeocodificacionApiService } from '../../services/geocodificacion-api.service';
import {
  AdvertenciaValidacion,
  CatalogoItem,
  DuplicadoConflictData,
  RegistrarAccidenteRequest,
} from '../../services/models/accidente.types';
import { UbicacionCatalogoApiService } from '../../services/ubicacion-catalogo-api.service';
import { SEVERIDADES } from '../../severidad.constants';
import { DuplicadoFusionDialog } from './duplicado-fusion.dialog';

const TIPOS_REPORTADO = [
  { value: 1, label: 'Llamada telefónica' },
  { value: 2, label: 'App móvil' },
  { value: 3, label: 'Integración API' },
  { value: 4, label: 'Cámara de tráfico' },
];

const GEOCODE_DEBOUNCE_MS = 500;
const DRAFT_DEBOUNCE_MS = 500;
const DRAFT_STORAGE_KEY = 'tsi.registro-accidente.draft';

type SyncStatus = 'live' | 'reconnecting' | 'offline';

function justificacionRetrospectivaValidator(group: {
  get(name: string): { value: unknown } | null;
}): ValidationErrors | null {
  const retrospectivo = group.get('registroRetrospectivo')?.value;
  const justificacion = (group.get('justificacionRetrospectiva')?.value as string) ?? '';
  if (retrospectivo && !justificacion.trim()) {
    return { justificacionRequerida: true };
  }
  return null;
}

@Component({
  selector: 'app-registro-accidente',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    FormsModule,
    DuplicadoFusionDialog,
    LocationPickerMapComponent,
    TablerIconComponent,
    DecimalPipe,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="mx-auto max-w-6xl p-8">
      <h1 class="m-0 mb-6 text-2xl font-bold text-text-primary">Registro de accidente</h1>

      @if (draftRestored()) {
        <p
          class="mb-4 rounded-md border border-alert-info bg-alert-info-bg px-4 py-3 text-sm text-alert-info"
          data-testid="draft-restored"
        >
          Se restauró un borrador guardado localmente (RNF-REG-006).
        </p>
      }

      @if (advertencias().length) {
        <div
          class="mb-4 rounded-md border border-alert-warning bg-alert-warning-bg px-4 py-3 text-sm text-alert-warning"
        >
          <p class="m-0 mb-2 font-semibold">Advertencias de validación</p>
          <ul class="m-0 list-disc pl-5" data-testid="advertencias">
            @for (a of advertencias(); track a.code) {
              <li>{{ a.detail }}</li>
            }
          </ul>
          <button
            type="button"
            class="mt-3 rounded-md border border-alert-warning px-3 py-1.5 text-sm font-medium text-alert-warning hover:bg-alert-warning-bg"
            (click)="confirmarBorrador()"
          >
            Confirmar reporte
          </button>
        </div>
      }

      <form [formGroup]="form" (ngSubmit)="registrar(false)" novalidate>
        <div class="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
          <!-- Columna izquierda -->
          <div class="grid gap-6">
            <section class="rounded-lg border border-border-default bg-bg-surface p-6">
              <div class="mb-4 flex items-center justify-between">
                <h2 class="m-0 text-base font-semibold text-text-primary">Ubicación y hora</h2>
                <span class="flex items-center gap-1.5 text-xs text-text-secondary" data-testid="sync-status">
                  <span
                    class="h-2 w-2 rounded-full"
                    [class.bg-alert-success]="syncStatus() === 'live'"
                    [class.bg-alert-warning]="syncStatus() === 'reconnecting'"
                    [class.bg-text-secondary]="syncStatus() === 'offline'"
                  ></span>
                  @switch (syncStatus()) {
                    @case ('live') {
                      En vivo
                    }
                    @case ('reconnecting') {
                      Reconectando…
                    }
                    @default {
                      Sin conexión — guardado localmente
                    }
                  }
                </span>
              </div>

              <app-location-picker-map
                [lat]="form.controls.latitudinicio.value"
                [lng]="form.controls.longitudinicio.value"
                (coordsChange)="onCoordsChange($event)"
              />

              <p class="mt-2 text-sm text-text-secondary">
                Lat: {{ form.controls.latitudinicio.value | number: '1.4-4' }} · Lon:
                {{ form.controls.longitudinicio.value | number: '1.4-4' }}
                @if (geocodificando()) {
                  <span> · Geocodificando…</span>
                } @else if (calleSugerida() !== null) {
                  <span> · Calle sugerida: <strong>{{ calleSugerida() }}</strong></span>
                  @if (fueraCobertura()) {
                    <span class="ml-1 text-alert-warning">(fuera de cobertura operativa)</span>
                  }
                }
              </p>

              <div
                class="mt-2 rounded-md px-3.5 py-2.5 text-sm"
                [class.bg-alert-critical-bg]="isInvalid('idcalle')"
                [class.text-alert-critical]="isInvalid('idcalle')"
                [class.bg-bg-page]="!isInvalid('idcalle')"
                [class.text-text-secondary]="!isInvalid('idcalle')"
              >
                Calle seleccionada (idcalle):
                <strong>{{ form.controls.idcalle.value || '— ninguna aún —' }}</strong>
              </div>

              <details class="mt-3">
                <summary class="cursor-pointer text-sm font-medium text-accent-primary">
                  ¿La geocodificación no encontró la calle correcta? Selecciónala manualmente
                </summary>

                <div class="mt-2 grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <div class="grid gap-1.5">
                    <label for="cascadaPais" class="text-sm font-medium text-text-secondary"
                      >País</label
                    >
                    <select
                      id="cascadaPais"
                      class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary"
                      [ngModel]="cascadaPais()"
                      [ngModelOptions]="{ standalone: true }"
                      (ngModelChange)="onCascadaPaisChange($event)"
                    >
                      <option [ngValue]="null">— Selecciona —</option>
                      @for (p of cascadaPaises(); track p.id) {
                        <option [ngValue]="p.id">{{ p.nombre }}</option>
                      }
                    </select>
                  </div>

                  <div class="grid gap-1.5">
                    <label for="cascadaEstado" class="text-sm font-medium text-text-secondary"
                      >Estado / región</label
                    >
                    <select
                      id="cascadaEstado"
                      class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary disabled:cursor-not-allowed disabled:opacity-60"
                      [ngModel]="cascadaEstado()"
                      [ngModelOptions]="{ standalone: true }"
                      (ngModelChange)="onCascadaEstadoChange($event)"
                      [disabled]="!cascadaPais()"
                    >
                      <option [ngValue]="null">— Selecciona —</option>
                      @for (e of cascadaEstados(); track e.id) {
                        <option [ngValue]="e.id">{{ e.nombre }}</option>
                      }
                    </select>
                  </div>

                  <div class="grid gap-1.5">
                    <label for="cascadaCondado" class="text-sm font-medium text-text-secondary"
                      >Condado</label
                    >
                    <select
                      id="cascadaCondado"
                      class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary disabled:cursor-not-allowed disabled:opacity-60"
                      [ngModel]="cascadaCondado()"
                      [ngModelOptions]="{ standalone: true }"
                      (ngModelChange)="onCascadaCondadoChange($event)"
                      [disabled]="!cascadaEstado()"
                    >
                      <option [ngValue]="null">— Selecciona —</option>
                      @for (c of cascadaCondados(); track c.id) {
                        <option [ngValue]="c.id">{{ c.nombre }}</option>
                      }
                    </select>
                  </div>

                  <div class="grid gap-1.5">
                    <label for="cascadaCiudad" class="text-sm font-medium text-text-secondary"
                      >Ciudad</label
                    >
                    <select
                      id="cascadaCiudad"
                      class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary disabled:cursor-not-allowed disabled:opacity-60"
                      [ngModel]="cascadaCiudad()"
                      [ngModelOptions]="{ standalone: true }"
                      (ngModelChange)="onCascadaCiudadChange($event)"
                      [disabled]="!cascadaCondado()"
                    >
                      <option [ngValue]="null">— Selecciona —</option>
                      @for (c of cascadaCiudades(); track c.id) {
                        <option [ngValue]="c.id">{{ c.nombre }}</option>
                      }
                    </select>
                  </div>

                  <div class="grid gap-1.5 sm:col-span-2">
                    <label for="cascadaCalle" class="text-sm font-medium text-text-secondary"
                      >Calle</label
                    >
                    <select
                      id="cascadaCalle"
                      class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary disabled:cursor-not-allowed disabled:opacity-60"
                      [ngModel]="null"
                      [ngModelOptions]="{ standalone: true }"
                      (ngModelChange)="onCascadaCalleChange($event)"
                      [disabled]="!cascadaCiudad()"
                    >
                      <option [ngValue]="null">— Selecciona —</option>
                      @for (c of cascadaCalles(); track c.id) {
                        <option [ngValue]="c.id">{{ c.nombre }}</option>
                      }
                    </select>
                  </div>
                </div>
              </details>

              <div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div class="grid gap-1.5">
                  <label for="codigopostal" class="text-sm font-medium text-text-secondary"
                    >Código postal</label
                  >
                  <input
                    id="codigopostal"
                    type="text"
                    class="w-full rounded-md border border-border-default px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
                    formControlName="codigopostal"
                  />
                </div>
                <div class="grid gap-1.5">
                  <label for="fechahoraaccidente" class="text-sm font-medium text-text-secondary"
                    >Fecha y hora del accidente</label
                  >
                  <input
                    id="fechahoraaccidente"
                    type="datetime-local"
                    class="w-full rounded-md border px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
                    [class.border-border-default]="!isInvalid('fechahoraaccidente')"
                    [class.border-alert-critical]="isInvalid('fechahoraaccidente')"
                    formControlName="fechahoraaccidente"
                    [attr.aria-invalid]="isInvalid('fechahoraaccidente')"
                  />
                </div>
              </div>

              <div class="mt-4 flex items-center gap-2">
                <input
                  id="registroRetrospectivo"
                  type="checkbox"
                  formControlName="registroRetrospectivo"
                />
                <label for="registroRetrospectivo" class="text-sm text-text-primary"
                  >Registro retrospectivo (más de 24 horas)</label
                >
              </div>

              @if (form.controls.registroRetrospectivo.value) {
                <div class="mt-3 grid gap-1.5">
                  <label
                    for="justificacionRetrospectiva"
                    class="text-sm font-medium text-text-secondary"
                    >Justificación del registro retrospectivo</label
                  >
                  <textarea
                    id="justificacionRetrospectiva"
                    rows="2"
                    class="w-full rounded-md border px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
                    [class.border-border-default]="
                      !form.errors?.['justificacionRequerida'] || !form.touched
                    "
                    [class.border-alert-critical]="
                      form.errors?.['justificacionRequerida'] && form.touched
                    "
                    formControlName="justificacionRetrospectiva"
                  ></textarea>
                </div>
              }
            </section>

            <section class="rounded-lg border border-border-default bg-bg-surface p-6">
              <h2 class="m-0 mb-4 text-base font-semibold text-text-primary">
                Narrativa del incidente
              </h2>
              <div class="grid gap-1.5">
                <label for="descripcion" class="text-sm font-medium text-text-secondary"
                  >Descripción</label
                >
                <textarea
                  id="descripcion"
                  rows="4"
                  class="w-full rounded-md border px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
                  [class.border-border-default]="!isInvalid('descripcion')"
                  [class.border-alert-critical]="isInvalid('descripcion')"
                  formControlName="descripcion"
                  [attr.aria-invalid]="isInvalid('descripcion')"
                ></textarea>
              </div>
            </section>
          </div>

          <!-- Columna derecha -->
          <div class="grid gap-6">
            <section class="rounded-lg border border-border-default bg-bg-surface p-6">
              <h2 class="m-0 mb-4 text-base font-semibold text-text-primary">
                Severidad e impacto inicial
              </h2>

              <div class="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Severidad">
                @for (s of severidades; track s.value) {
                  <button
                    type="button"
                    class="inline-flex items-center justify-center gap-1.5 rounded-md border px-3 py-2.5 text-sm font-semibold transition-colors"
                    [class.border-border-default]="form.controls.idseveridad.value !== s.value"
                    [class.text-text-secondary]="form.controls.idseveridad.value !== s.value"
                    [class.border-alert-success]="form.controls.idseveridad.value === s.value && s.tone === 'success'"
                    [class.text-alert-success]="form.controls.idseveridad.value === s.value && s.tone === 'success'"
                    [class.bg-alert-success-bg]="form.controls.idseveridad.value === s.value && s.tone === 'success'"
                    [class.border-alert-warning]="form.controls.idseveridad.value === s.value && s.tone === 'warning'"
                    [class.text-alert-warning]="form.controls.idseveridad.value === s.value && s.tone === 'warning'"
                    [class.bg-alert-warning-bg]="form.controls.idseveridad.value === s.value && s.tone === 'warning'"
                    [class.border-alert-urgent]="form.controls.idseveridad.value === s.value && s.tone === 'urgent'"
                    [class.text-alert-urgent]="form.controls.idseveridad.value === s.value && s.tone === 'urgent'"
                    [class.bg-alert-urgent-bg]="form.controls.idseveridad.value === s.value && s.tone === 'urgent'"
                    [class.border-alert-critical]="form.controls.idseveridad.value === s.value && s.tone === 'critical'"
                    [class.text-alert-critical]="form.controls.idseveridad.value === s.value && s.tone === 'critical'"
                    [class.bg-alert-critical-bg]="form.controls.idseveridad.value === s.value && s.tone === 'critical'"
                    [attr.aria-pressed]="form.controls.idseveridad.value === s.value"
                    (click)="form.controls.idseveridad.setValue(s.value)"
                  >
                    <app-tabler-icon [name]="s.icon" [size]="16" />
                    {{ s.label }}
                  </button>
                }
              </div>

              <div class="mt-4 grid grid-cols-2 gap-4">
                <div class="grid gap-1.5">
                  <label for="numvehiculos" class="text-sm font-medium text-text-secondary"
                    >Vehículos involucrados</label
                  >
                  <input
                    id="numvehiculos"
                    type="number"
                    min="0"
                    class="w-full [appearance:textfield] rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                    formControlName="numvehiculos"
                  />
                </div>
                <div class="grid gap-1.5">
                  <label for="numheridos" class="text-sm font-medium text-text-secondary"
                    >Heridos</label
                  >
                  <input
                    id="numheridos"
                    type="number"
                    min="0"
                    class="w-full [appearance:textfield] rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                    formControlName="numheridos"
                  />
                </div>
                <div class="grid gap-1.5">
                  <label for="numvictimas" class="text-sm font-medium text-text-secondary"
                    >Víctimas (total)</label
                  >
                  <input
                    id="numvictimas"
                    type="number"
                    min="0"
                    class="w-full [appearance:textfield] rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                    formControlName="numvictimas"
                  />
                </div>
                <div class="grid gap-1.5">
                  <label for="numfallecidos" class="text-sm font-medium text-text-secondary"
                    >Fallecidos</label
                  >
                  <input
                    id="numfallecidos"
                    type="number"
                    min="0"
                    class="w-full [appearance:textfield] rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                    formControlName="numfallecidos"
                  />
                </div>
              </div>
            </section>

            <section class="rounded-lg border border-border-default bg-bg-surface p-6">
              <h2 class="m-0 mb-4 text-base font-semibold text-text-primary">Origen del reporte</h2>
              <div class="grid gap-1.5">
                <label for="idtiporeportado" class="text-sm font-medium text-text-secondary"
                  >Tipo de reporte</label
                >
                <select
                  id="idtiporeportado"
                  class="w-full rounded-md border border-border-default bg-bg-surface px-3.5 py-2.5 text-text-primary focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-accent-primary"
                  formControlName="idtiporeportado"
                >
                  <option [value]="null">— Sin especificar —</option>
                  @for (t of tiposReportado; track t.value) {
                    <option [value]="t.value">{{ t.label }}</option>
                  }
                </select>
              </div>
            </section>

            <div class="grid gap-3">
              <button
                type="submit"
                class="inline-flex items-center justify-center gap-2 rounded-md bg-accent-primary px-5 py-3 font-semibold text-white [&:hover:not(:disabled)]:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-60"
                [disabled]="form.invalid || loading()"
              >
                {{ loading() ? 'Registrando…' : 'Registrar accidente' }}
              </button>
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 rounded-md border border-border-default px-5 py-3 font-semibold text-text-primary hover:bg-bg-page disabled:cursor-not-allowed disabled:opacity-60"
                [disabled]="form.invalid || loading()"
                (click)="registrar(true)"
              >
                {{ loading() ? 'Registrando…' : 'Registrar forzando advertencias' }}
              </button>
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 rounded-md px-5 py-2 text-sm font-medium text-text-secondary hover:text-text-primary"
                (click)="cancelar()"
              >
                Cancelar registro
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>

    @if (duplicadoConflicto()) {
      <app-duplicado-fusion-dialog
        [idPrincipalSugerido]="duplicadoConflicto()!.idaccidente_principal_sugerido ?? ''"
        (confirmar)="confirmarFusion($event)"
        (cancelar)="duplicadoConflicto.set(null)"
      />
    }
  `,
})
export class RegistroAccidentePage {
  private readonly accidenteApi = inject(AccidenteApiService);
  private readonly geocodificacionApi = inject(GeocodificacionApiService);
  private readonly ubicacionCatalogo = inject(UbicacionCatalogoApiService);
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  private readonly notifications = inject(NotificationService);

  readonly severidades = SEVERIDADES;
  readonly tiposReportado = TIPOS_REPORTADO;

  readonly loading = signal(false);
  readonly geocodificando = signal(false);
  readonly advertencias = signal<AdvertenciaValidacion[]>([]);
  readonly calleSugerida = signal<number | null>(null);
  readonly fueraCobertura = signal(false);
  readonly duplicadoConflicto = signal<DuplicadoConflictData | null>(null);

  // Resiliencia de captura ante interrupción de red (RNF-REG-006, design-system.md §2 y §5
  // "Indicador de sincronización/conexión"). El formulario se autoguarda en localStorage
  // mientras el registro no se haya confirmado, y se restaura si la pestaña se recarga.
  readonly syncStatus = signal<SyncStatus>(navigator.onLine ? 'live' : 'offline');
  readonly draftRestored = signal(false);
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  // Cascada manual de ubicación (RF-REG-006 punto 3, Escenario 5).
  // Solo sirve para ayudar al Operador a encontrar el idcalle correcto; lo único
  // que se envía al backend sigue siendo idcalle (RF-REG-001), sin cambios de modelo.
  readonly cascadaPais = signal<number | null>(null);
  readonly cascadaEstado = signal<number | null>(null);
  readonly cascadaCondado = signal<number | null>(null);
  readonly cascadaCiudad = signal<number | null>(null);

  readonly cascadaPaises = signal<CatalogoItem[]>([]);
  readonly cascadaEstados = signal<CatalogoItem[]>([]);
  readonly cascadaCondados = signal<CatalogoItem[]>([]);
  readonly cascadaCiudades = signal<CatalogoItem[]>([]);
  readonly cascadaCalles = signal<CatalogoItem[]>([]);

  private idaccidenteBorrador: string | null = null;
  private geocodeTimer: ReturnType<typeof setTimeout> | null = null;

  readonly form = this.fb.nonNullable.group(
    {
      latitudinicio: [0, [Validators.required, Validators.min(-90), Validators.max(90)]],
      longitudinicio: [0, [Validators.required, Validators.min(-180), Validators.max(180)]],
      fechahoraaccidente: [this.defaultDatetimeLocal(), [Validators.required]],
      idseveridad: [2, [Validators.required]],
      descripcion: ['', [Validators.required]],
      idcalle: [0, [Validators.required, Validators.min(1)]],
      codigopostal: [''],
      numvehiculos: [0],
      numheridos: [0],
      numvictimas: [0],
      numfallecidos: [0],
      idtiporeportado: [null as number | null],
      registroRetrospectivo: [false],
      justificacionRetrospectiva: [''],
    },
    { validators: justificacionRetrospectivaValidator },
  );

  constructor() {
    this.ubicacionCatalogo.listarPaises().subscribe((paises) => this.cascadaPaises.set(paises));
    this.restaurarBorrador();

    this.form.valueChanges
      .pipe(debounceTime(DRAFT_DEBOUNCE_MS), takeUntilDestroyed(this.destroyRef))
      .subscribe((value) => this.guardarBorrador(value));

    const onOnline = () => {
      this.syncStatus.set('reconnecting');
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
      }
      this.reconnectTimer = setTimeout(() => this.syncStatus.set('live'), 1000);
    };
    const onOffline = () => this.syncStatus.set('offline');

    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    this.destroyRef.onDestroy(() => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
      }
    });
  }

  private guardarBorrador(value: unknown): void {
    try {
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(value));
    } catch {
      // localStorage no disponible (modo privado, cuota excedida, etc.) — no bloquea el registro.
    }
  }

  private restaurarBorrador(): void {
    let raw: string | null = null;
    try {
      raw = localStorage.getItem(DRAFT_STORAGE_KEY);
    } catch {
      return;
    }
    if (!raw) {
      return;
    }
    try {
      const draft = JSON.parse(raw);
      this.form.patchValue(draft);
      this.draftRestored.set(true);
    } catch {
      // Borrador corrupto — se ignora silenciosamente.
    }
  }

  private limpiarBorrador(): void {
    try {
      localStorage.removeItem(DRAFT_STORAGE_KEY);
    } catch {
      // No-op si localStorage no está disponible.
    }
    this.draftRestored.set(false);
  }

  isInvalid(controlName: keyof typeof this.form.controls): boolean {
    const control = this.form.controls[controlName];
    return control.invalid && (control.touched || control.dirty);
  }

  onCascadaPaisChange(idpais: number | null): void {
    this.cascadaPais.set(idpais);
    this.cascadaEstado.set(null);
    this.cascadaCondado.set(null);
    this.cascadaCiudad.set(null);
    this.cascadaEstados.set([]);
    this.cascadaCondados.set([]);
    this.cascadaCiudades.set([]);
    this.cascadaCalles.set([]);
    if (idpais) {
      this.ubicacionCatalogo.listarEstados(idpais).subscribe((e) => this.cascadaEstados.set(e));
    }
  }

  onCascadaEstadoChange(idestado: number | null): void {
    this.cascadaEstado.set(idestado);
    this.cascadaCondado.set(null);
    this.cascadaCiudad.set(null);
    this.cascadaCondados.set([]);
    this.cascadaCiudades.set([]);
    this.cascadaCalles.set([]);
    if (idestado) {
      this.ubicacionCatalogo.listarCondados(idestado).subscribe((c) => this.cascadaCondados.set(c));
    }
  }

  onCascadaCondadoChange(idcondado: number | null): void {
    this.cascadaCondado.set(idcondado);
    this.cascadaCiudad.set(null);
    this.cascadaCiudades.set([]);
    this.cascadaCalles.set([]);
    if (idcondado) {
      this.ubicacionCatalogo.listarCiudades(idcondado).subscribe((c) => this.cascadaCiudades.set(c));
    }
  }

  onCascadaCiudadChange(idciudad: number | null): void {
    this.cascadaCiudad.set(idciudad);
    this.cascadaCalles.set([]);
    if (idciudad) {
      this.ubicacionCatalogo.listarCalles(idciudad).subscribe((c) => this.cascadaCalles.set(c));
    }
  }

  onCascadaCalleChange(idcalle: number | null): void {
    if (idcalle) {
      this.form.controls.idcalle.setValue(idcalle);
      this.form.controls.idcalle.markAsTouched();
    }
  }

  private defaultDatetimeLocal(): string {
    const now = new Date(Date.now() - new Date().getTimezoneOffset() * 60000);
    return now.toISOString().slice(0, 16);
  }

  onCoordsChange(coords: LatLng): void {
    this.form.patchValue({ latitudinicio: coords.lat, longitudinicio: coords.lng });

    if (this.geocodeTimer) {
      clearTimeout(this.geocodeTimer);
    }
    this.geocodeTimer = setTimeout(() => this.geocodificar(coords), GEOCODE_DEBOUNCE_MS);
  }

  private geocodificar(coords: LatLng): void {
    this.geocodificando.set(true);
    this.geocodificacionApi
      .sugerir(coords.lat, coords.lng)
      .pipe(finalize(() => this.geocodificando.set(false)))
      .subscribe({
        next: (res) => {
          this.calleSugerida.set(res.data.idcalle);
          this.fueraCobertura.set(!res.data.en_cobertura_operativa);
          if (res.data.idcalle) {
            this.form.controls.idcalle.setValue(res.data.idcalle);
          }
        },
      });
  }

  registrar(forzarAdvertencias: boolean): void {
    this.form.markAllAsTouched();
    if (this.form.invalid || this.loading()) {
      return;
    }

    const raw = this.form.getRawValue();
    const payload: RegistrarAccidenteRequest = {
      latitudinicio: raw.latitudinicio,
      longitudinicio: raw.longitudinicio,
      fechahoraaccidente: new Date(raw.fechahoraaccidente).getTime(),
      idseveridad: raw.idseveridad as 1 | 2 | 3 | 4,
      descripcion: raw.descripcion,
      idcalle: raw.idcalle,
      codigopostal: raw.codigopostal || undefined,
      numvehiculos: raw.numvehiculos || undefined,
      numheridos: raw.numheridos || undefined,
      numvictimas: raw.numvictimas || undefined,
      numfallecidos: raw.numfallecidos || undefined,
      idtiporeportado: raw.idtiporeportado ?? undefined,
      registroRetrospectivo: raw.registroRetrospectivo || undefined,
      justificacionRetrospectiva: raw.justificacionRetrospectiva || undefined,
    };

    this.loading.set(true);
    this.duplicadoConflicto.set(null);

    this.accidenteApi
      .registrar(payload, forzarAdvertencias)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (res) => {
          this.notifications.toast(`Accidente registrado (${res.data.idaccidente})`, 'success');
          this.advertencias.set(res.data.advertencias ?? []);
          if (res.data.estado === 'BORRADOR') {
            this.idaccidenteBorrador = res.data.idaccidente;
          } else {
            this.limpiarBorrador();
          }
        },
        error: (err: HttpErrorResponse) => {
          const body = err.error as Partial<DuplicadoConflictData> | undefined;
          if (err.status === 409 && body?.idaccidente_duplicado_sugerido) {
            this.duplicadoConflicto.set(body as DuplicadoConflictData);
            return;
          }
          this.notifications.alert(
            'No se pudo registrar el accidente. Verifica la conexión e inténtalo de nuevo.',
            'Error al registrar',
          );
        },
      });
  }

  confirmarFusion(idPrincipalElegido: string): void {
    const conflicto = this.duplicadoConflicto();
    if (!conflicto?.idaccidente_duplicado_sugerido) {
      return;
    }
    this.accidenteApi
      .fusionar(conflicto.idaccidente_duplicado_sugerido, {
        idaccidenteprincipal: idPrincipalElegido,
        confirmacion: true,
      })
      .subscribe({
        next: (res) => {
          this.notifications.toast(res.data.message, 'success');
          this.duplicadoConflicto.set(null);
        },
        error: () => this.notifications.alert('No se pudo fusionar los reportes.', 'Error al fusionar'),
      });
  }

  confirmarBorrador(): void {
    if (!this.idaccidenteBorrador) {
      return;
    }
    this.accidenteApi.confirmarReporte(this.idaccidenteBorrador, { confirmacion: true }).subscribe({
      next: (res) => {
        this.notifications.toast(res.data.message, 'success');
        this.advertencias.set([]);
        this.limpiarBorrador();
      },
    });
  }

  cancelar(): void {
    void this.router.navigate(['/accidentes/lista']);
  }
}
