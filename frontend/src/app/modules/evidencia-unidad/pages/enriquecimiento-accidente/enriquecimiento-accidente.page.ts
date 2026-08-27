import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ConnectivityService } from '../../../../shared/connectivity/connectivity.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import {
  primerError,
  validarCedula,
  validarEntero,
  validarNombre,
  validarRequerido,
} from '../../../../shared/validacion/campos.validacion';
import { EnriquecimientoApiService } from '../../services/enriquecimiento-api.service';
import { EvidenciaSyncSchedulerService } from '../../services/evidencia-sync-scheduler.service';
import {
  CatalogoItem,
  ConductorAccidenteItem,
  ElementoFisicoAccidenteItem,
  EnriquecimientoAccidenteData,
  ImplicadoItem,
  EstadoImplicado,
  TipoImplicado,
} from '../../services/models/evidencia-unidad.types';

/** Columnas booleanas de `Dim_Estado_Conductor`. */
type EjeEstadoConductor =
  | 'estadosobriedad'
  | 'nivelatencion'
  | 'condicionfisica'
  | 'usoseguridad';

interface EjeEstadoConductorUI {
  campo: EjeEstadoConductor;
  etiqueta: string;
  /** Cómo se lee el valor `true` de la columna. */
  siEtiqueta: string;
  /** Cómo se lee el valor `false`. */
  noEtiqueta: string;
}

/**
 * Los cuatro ejes del estado del conductor, **con sus dos lados escritos**.
 *
 * El modelo guarda booleanos, pero un booleano solo es legible si se nombra lo
 * que significa cada valor. La revisión (hallazgo #5) lo puso así: «en vez de
 * sobrio se le cambia a estado de ebriedad, depende de cómo el usuario pueda
 * percibir mejor la opción que va a seleccionar». Una casilla "Sobrio" obliga a
 * deducir qué afirma desmarcarla; dos opciones con nombre no.
 *
 * ⚠️ El orden `true`/`false` de cada eje debe coincidir con la semántica de
 * `Dim_Estado_Conductor`: `true` es siempre la condición favorable.
 */
const EJES_ESTADO_CONDUCTOR: EjeEstadoConductorUI[] = [
  {
    campo: 'estadosobriedad',
    etiqueta: 'Estado de sobriedad',
    siEtiqueta: 'Sobrio',
    noEtiqueta: 'Bajo efectos de alcohol o sustancias',
  },
  {
    campo: 'nivelatencion',
    etiqueta: 'Nivel de atención',
    siEtiqueta: 'Atento a la vía',
    noEtiqueta: 'Distraído',
  },
  {
    campo: 'condicionfisica',
    etiqueta: 'Condición física',
    siEtiqueta: 'Ileso',
    noEtiqueta: 'Lesionado o impedido',
  },
  {
    campo: 'usoseguridad',
    etiqueta: 'Dispositivo de seguridad',
    siEtiqueta: 'Lo usaba',
    noEtiqueta: 'No lo usaba',
  },
];

@Component({
  selector: 'app-enriquecimiento-accidente',
  standalone: true,
  imports: [RouterLink, FormsModule, TablerIconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './enriquecimiento-accidente.page.html',
})
export class EnriquecimientoAccidentePage implements OnInit {
  private readonly api = inject(EnriquecimientoApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly syncScheduler = inject(EvidenciaSyncSchedulerService);
  private readonly notifications = inject(NotificationService);
  readonly connectivity = inject(ConnectivityService);

  idaccidente = '';
  /** Solo consulta cuando se abre desde Detalles (`?mode=view`). */
  readonly soloLectura = signal(false);
  readonly data = signal<EnriquecimientoAccidenteData | null>(null);
  readonly periodos = signal<CatalogoItem[]>([]);
  readonly climas = signal<CatalogoItem[]>([]);
  readonly elementosCatalogo = signal<CatalogoItem[]>([]);
  readonly estadosConductor = signal<CatalogoItem[]>([]);
  readonly error = signal('');
  readonly cargando = signal(true);
  readonly guardando = signal(false);

  idperiododia: number | null = null;
  idestadoclima: number | null = null;
  idelementofisico: number | null = null;

  /** Dim_Conductor — required */
  identificacion = '';
  nombres = '';
  apellidos = '';
  /**
   * Catálogos cerrados. Deben coincidir con `GENEROS` / `ESTADOS_LICENCIA` de
   * `EnriquecimientoConductorService`: el backend los rechaza si no.
   */
  readonly generos = ['Masculino', 'Femenino', 'Otro', 'No informa'];
  readonly estadosLicencia = ['Vigente', 'Caducada', 'Suspendida', 'Sin licencia'];

  /** Dim_Conductor — optional */
  genero = '';
  tipolicencia = '';
  estadolicencia = '';
  ciudadresidencia = '';
  aniosexperiencia: number | null = null;
  /**
   * Estado del conductor. Cada eje se resuelve a `idestadoconductor` por match
   * exacto contra `Dim_Estado_Conductor`.
   *
   * ⚠️ Arranca **sin decidir** (`null`), no en `true`.
   *
   * Antes eran cuatro casillas marcadas por defecto, así que no tocar nada
   * afirmaba que el conductor estaba sobrio, atento, ileso y con cinturón — la
   * declaración que más pesa en un siniestro, hecha por omisión. Y desmarcar una
   * casilla exigía adivinar qué significaba lo contrario (hallazgo #5).
   */
  estadoConductor: Record<EjeEstadoConductor, boolean | null> = {
    estadosobriedad: null,
    nivelatencion: null,
    condicionfisica: null,
    usoseguridad: null,
  };

  readonly ejesEstadoConductor = EJES_ESTADO_CONDUCTOR;
  /** Dim_Vehiculo — required */
  tipovehiculo = '';
  /** Dim_Vehiculo — optional */
  modelovehiculo = '';
  categoriausovehiculo = '';
  mercanciapeligrosa = false;
  ejes: number | null = null;

  /** Dim_Implicado — ontología */
  tipoimplicado: TipoImplicado | '' = '';
  estadoimplicado: EstadoImplicado | '' = '';
  implicadoGenero = '';
  implicadoEdad: number | null = null;

  ngOnInit(): void {
    this.idaccidente = this.route.snapshot.paramMap.get('idaccidente') ?? '';
    this.soloLectura.set(this.route.snapshot.queryParamMap.get('mode') === 'view');
    this.syncScheduler.registrarCaso(this.idaccidente);
    this.cargarCatalogos();
    this.recargar();
  }

  recargar(): void {
    this.error.set('');
    this.cargando.set(true);
    this.api.consultar(this.idaccidente).subscribe({
      next: (res) => {
        this.data.set(res.data);
        this.idperiododia = res.data.clima?.idperiododia ?? null;
        this.idestadoclima = res.data.clima?.idestadoclima ?? null;
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar el enriquecimiento del caso');
        this.cargando.set(false);
      },
    });
  }

  guardarClima(): void {
    if (this.soloLectura()) {
      return;
    }
    if (this.idperiododia == null && this.idestadoclima == null) {
      this.notifications.alert('Seleccione período o clima', 'Validación');
      return;
    }
    this.guardando.set(true);
    this.api
      .upsertClima(this.idaccidente, {
        idperiododia: this.idperiododia,
        idestadoclima: this.idestadoclima,
      })
      .subscribe({
        next: () => {
          this.notifications.toast(
            this.connectivity.online()
              ? 'Clima actualizado'
              : 'Clima guardado localmente (sin conexión)',
            'success',
          );
          this.guardando.set(false);
          if (this.connectivity.online()) {
            this.recargar();
          }
        },
        error: () => {
          this.notifications.alert('No se pudo guardar el clima', 'Error');
          this.guardando.set(false);
        },
      });
  }

  agregarFisico(): void {
    if (this.soloLectura()) {
      return;
    }
    if (this.idelementofisico == null) {
      this.notifications.alert('Seleccione un elemento físico', 'Validación');
      return;
    }
    this.guardando.set(true);
    this.api
      .agregarElementoFisico(this.idaccidente, { idelementofisico: this.idelementofisico })
      .subscribe({
        next: () => {
          this.notifications.toast(
            this.connectivity.online()
              ? 'Elemento físico agregado'
              : 'Elemento guardado localmente (sin conexión)',
            'success',
          );
          this.idelementofisico = null;
          this.guardando.set(false);
          if (this.connectivity.online()) {
            this.recargar();
          }
        },
        error: () => {
          this.notifications.alert('No se pudo agregar el elemento', 'Error');
          this.guardando.set(false);
        },
      });
  }

  desactivarFisico(item: ElementoFisicoAccidenteItem): void {
    if (this.soloLectura()) {
      return;
    }
    this.api.desactivarElementoFisico(this.idaccidente, item.idelementosfisicosaccidente).subscribe({
      next: () => {
        this.notifications.toast('Elemento desactivado', 'success');
        this.recargar();
      },
      error: () => this.notifications.alert('No se pudo desactivar', 'Error'),
    });
  }

  registrarConductor(): void {
    if (this.soloLectura()) {
      return;
    }
    // RN-VAL-CAMPOS — formato, no solo presencia. Antes bastaba con que los
    // campos no estuvieran vacíos: la cédula aceptaba letras (hallazgo #9).
    // El espejo de estas mismas reglas está en el servicio de backend.
    const errorCampos = primerError(
      validarCedula(this.identificacion),
      validarNombre(this.nombres, 'Nombres'),
      validarNombre(this.apellidos, 'Apellidos'),
      validarNombre(this.ciudadresidencia, 'Ciudad de residencia', { requerido: false }),
      validarEntero(this.aniosexperiencia, 'Años de experiencia', { min: 0, max: 80 }),
      validarEntero(this.ejes, 'Ejes', { min: 1, max: 20 }),
      validarRequerido(this.tipovehiculo, 'Tipo de vehículo'),
    );
    if (errorCampos) {
      this.notifications.alert(errorCampos, 'Validación');
      return;
    }
    if (!this.estadoConductorCompleto()) {
      // Se distingue de la falla de catálogo: son dos problemas distintos y el
      // mensaje único ("no hay estado en catálogo para esa combinación de
      // flags") no le decía nada a la unidad en ninguno de los dos casos.
      this.notifications.alert(
        `Declare el estado del conductor. Falta: ${this.ejesPendientes()}.`,
        'Validación',
      );
      return;
    }
    const idestadoconductor = this.resolveEstadoConductorId();
    if (idestadoconductor == null) {
      this.notifications.alert(
        'Esa combinación de estado del conductor no existe en el catálogo. ' +
          'Avise al administrador para que la registre.',
        'Catálogo incompleto',
      );
      return;
    }
    this.guardando.set(true);
    this.api
      .registrarConductor(this.idaccidente, {
        conductor: {
          identificacion: this.identificacion.trim(),
          nombres: this.nombres.trim(),
          apellidos: this.apellidos.trim(),
          genero: this.optionalText(this.genero),
          tipolicencia: this.optionalText(this.tipolicencia),
          estadolicencia: this.optionalText(this.estadolicencia),
          ciudadresidencia: this.optionalText(this.ciudadresidencia),
          aniosexperiencia: this.aniosexperiencia,
        },
        idestadoconductor,
        vehiculo: {
          tipovehiculo: this.tipovehiculo.trim(),
          modelovehiculo: this.optionalText(this.modelovehiculo),
          categoriausovehiculo: this.optionalText(this.categoriausovehiculo),
          mercanciapeligrosa: this.mercanciapeligrosa,
          ejes: this.ejes,
        },
      })
      .subscribe({
        next: () => {
          this.notifications.toast(
            this.connectivity.online()
              ? 'Conductor registrado'
              : 'Conductor cifrado y guardado localmente',
            'success',
          );
          this.resetFormularioConductor();
          this.guardando.set(false);
          if (this.connectivity.online()) {
            this.recargar();
          }
        },
        error: () => {
          this.notifications.alert('No se pudo registrar el conductor', 'Error');
          this.guardando.set(false);
        },
      });
  }

  desactivarConductor(item: ConductorAccidenteItem): void {
    if (this.soloLectura()) {
      return;
    }
    this.api.desactivarConductor(this.idaccidente, item.idconductoraccidente).subscribe({
      next: () => {
        this.notifications.toast('Conductor desactivado', 'success');
        this.recargar();
      },
      error: () => this.notifications.alert('No se pudo desactivar', 'Error'),
    });
  }

  registrarImplicado(): void {
    if (this.soloLectura()) {
      return;
    }
    if (!this.tipoimplicado || !this.estadoimplicado) {
      this.notifications.alert(
        'Complete tipo y estado del implicado',
        'Validación',
      );
      return;
    }
    this.guardando.set(true);
    this.api
      .registrarImplicado(this.idaccidente, {
        tipoimplicado: this.tipoimplicado,
        estadoimplicado: this.estadoimplicado,
        genero: this.optionalText(this.implicadoGenero),
        edad: this.implicadoEdad,
      })
      .subscribe({
        next: () => {
          this.notifications.toast(
            this.connectivity.online()
              ? 'Implicado registrado'
              : 'Implicado guardado localmente (pendiente de sync)',
            'success',
          );
          this.resetFormularioImplicado();
          this.guardando.set(false);
          if (this.connectivity.online()) {
            this.recargar();
          }
        },
        error: () => {
          this.notifications.alert('No se pudo registrar el implicado', 'Error');
          this.guardando.set(false);
        },
      });
  }

  desactivarImplicado(item: ImplicadoItem): void {
    if (this.soloLectura()) {
      return;
    }
    this.api.desactivarImplicado(this.idaccidente, item.idimplicado).subscribe({
      next: () => {
        this.notifications.toast('Implicado desactivado', 'success');
        this.recargar();
      },
      error: () => this.notifications.alert('No se pudo desactivar', 'Error'),
    });
  }

  catalogLabel(item: CatalogoItem, idKey: string, nameKey: string): string {
    const value = item[nameKey] ?? item[idKey];
    if (typeof value === 'boolean') {
      return value ? 'Sí' : 'No';
    }
    return String(value ?? '');
  }

  /** Label humano para Dim_Estado_Conductor (campos BOOLEAN en Pinot). */
  estadoConductorLabel(item: CatalogoItem): string {
    return [
      this.asBool(item['estadosobriedad']) ? 'Sobrio' : 'No sobrio',
      this.asBool(item['nivelatencion']) ? 'Atento' : 'Desatento',
      this.asBool(item['condicionfisica']) ? 'Ileso' : 'Lesionado',
      this.asBool(item['usoseguridad']) ? 'Con seguridad' : 'Sin seguridad',
    ].join(' · ');
  }

  estadoConductorLabelById(id: number | null | undefined): string {
    if (id == null) {
      return '';
    }
    const item = this.estadosConductor().find((e) => Number(e['idestadoconductor']) === Number(id));
    return item ? this.estadoConductorLabel(item) : `Estado #${id}`;
  }

  /** Resuelve idestadoconductor por match exacto de los 4 flags BOOLEAN. */
  setEstadoConductor(campo: EjeEstadoConductor, valor: boolean): void {
    this.estadoConductor = { ...this.estadoConductor, [campo]: valor };
  }

  estadoConductorCompleto(): boolean {
    return EJES_ESTADO_CONDUCTOR.every((eje) => this.estadoConductor[eje.campo] !== null);
  }

  /** Nombra los ejes que faltan, para que el aviso diga qué falta y no solo que falta algo. */
  ejesPendientes(): string {
    return EJES_ESTADO_CONDUCTOR.filter((eje) => this.estadoConductor[eje.campo] === null)
      .map((eje) => eje.etiqueta.toLowerCase())
      .join(', ');
  }

  resolveEstadoConductorId(): number | null {
    if (!this.estadoConductorCompleto()) {
      return null;
    }
    const match = this.estadosConductor().find((e) =>
      EJES_ESTADO_CONDUCTOR.every(
        (eje) => this.asBool(e[eje.campo]) === this.estadoConductor[eje.campo],
      ),
    );
    if (!match) {
      return null;
    }
    const id = Number(match['idestadoconductor']);
    return Number.isFinite(id) ? id : null;
  }

  private asBool(value: unknown): boolean {
    return value === true || value === 'true' || value === 1 || value === '1';
  }

  private optionalText(value: string): string | null {
    const trimmed = value.trim();
    return trimmed ? trimmed : null;
  }

  private resetFormularioConductor(): void {
    this.identificacion = '';
    this.nombres = '';
    this.apellidos = '';
    this.genero = '';
    this.tipolicencia = '';
    this.estadolicencia = '';
    this.ciudadresidencia = '';
    this.aniosexperiencia = null;
    // Vuelve a "sin decidir": el conductor siguiente es otra persona y su estado
    // hay que declararlo de nuevo, no heredarlo del anterior.
    this.estadoConductor = {
      estadosobriedad: null,
      nivelatencion: null,
      condicionfisica: null,
      usoseguridad: null,
    };
    this.tipovehiculo = '';
    this.modelovehiculo = '';
    this.categoriausovehiculo = '';
    this.mercanciapeligrosa = false;
    this.ejes = null;
  }

  private resetFormularioImplicado(): void {
    this.tipoimplicado = '';
    this.estadoimplicado = '';
    this.implicadoGenero = '';
    this.implicadoEdad = null;
  }

  private cargarCatalogos(): void {
    this.api.catalogoPeriodos().subscribe({
      next: (r) => this.periodos.set(r.data.items),
    });
    this.api.catalogoClimas().subscribe({
      next: (r) => this.climas.set(r.data.items),
    });
    this.api.catalogoElementosFisicos().subscribe({
      next: (r) => this.elementosCatalogo.set(r.data.items),
    });
    this.api.catalogoEstadosConductor().subscribe({
      next: (r) => this.estadosConductor.set(r.data.items),
    });
  }
}
