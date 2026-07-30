import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ConnectivityService } from '../../../../shared/connectivity/connectivity.service';
import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
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
  /** Dim_Conductor — optional */
  genero = '';
  tipolicencia = '';
  estadolicencia = '';
  ciudadresidencia = '';
  aniosexperiencia: number | null = null;
  /** Flags UI → se resuelven a idestadoconductor por match exacto en catálogo. */
  estadosobriedad = true;
  nivelatencion = true;
  condicionfisica = true;
  usoseguridad = true;
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
    if (!this.identificacion.trim() || !this.nombres.trim() || !this.apellidos.trim()) {
      this.notifications.alert(
        'Identificación, nombres y apellidos son requeridos',
        'Validación',
      );
      return;
    }
    if (!this.tipovehiculo.trim()) {
      this.notifications.alert('Tipo de vehículo es requerido', 'Validación');
      return;
    }
    const idestadoconductor = this.resolveEstadoConductorId();
    if (idestadoconductor == null) {
      this.notifications.alert(
        'No hay un estado de conductor en catálogo para esa combinación de flags',
        'Validación',
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
  resolveEstadoConductorId(): number | null {
    const match = this.estadosConductor().find(
      (e) =>
        this.asBool(e['estadosobriedad']) === this.estadosobriedad &&
        this.asBool(e['nivelatencion']) === this.nivelatencion &&
        this.asBool(e['condicionfisica']) === this.condicionfisica &&
        this.asBool(e['usoseguridad']) === this.usoseguridad,
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
    this.estadosobriedad = true;
    this.nivelatencion = true;
    this.condicionfisica = true;
    this.usoseguridad = true;
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
