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
import { RegistroAccidenteDraftService } from './registro-accidente-draft.service';

const TIPOS_REPORTADO = [
  { value: 1, label: 'Llamada telefónica' },
  { value: 2, label: 'App móvil' },
  { value: 3, label: 'Integración API' },
  { value: 4, label: 'Cámara de tráfico' },
];

const GEOCODE_DEBOUNCE_MS = 500;
const DRAFT_DEBOUNCE_MS = 500;

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
  templateUrl: './registro-accidente.page.html',
})
export class RegistroAccidentePage {
  private readonly accidenteApi = inject(AccidenteApiService);
  private readonly geocodificacionApi = inject(GeocodificacionApiService);
  private readonly ubicacionCatalogo = inject(UbicacionCatalogoApiService);
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  private readonly notifications = inject(NotificationService);
  private readonly draftService = inject(RegistroAccidenteDraftService);

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
      .subscribe((value) => this.draftService.guardar(value));

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

  private restaurarBorrador(): void {
    const draft = this.draftService.restaurar();
    if (draft === null) {
      return;
    }
    this.form.patchValue(draft as Partial<typeof this.form.value>);
    this.draftRestored.set(true);
  }

  private limpiarBorrador(): void {
    this.draftService.limpiar();
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
          const body = err.error?.data as Partial<DuplicadoConflictData> | undefined;
          if (err.status === 409 && body?.error === 'duplicado_posible' && body?.idaccidente_similar) {
            this.duplicadoConflicto.set(body as DuplicadoConflictData);
            return;
          }
          if (err.status === 409 && body?.error === 'fuera_cobertura') {
            this.notifications.alert(
              body.detail ?? 'La ubicación está fuera de la cobertura operativa.',
              'Fuera de cobertura',
            );
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
    if (!conflicto?.idaccidente_similar) {
      return;
    }
    this.accidenteApi
      .fusionar(conflicto.idaccidente_similar, {
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
