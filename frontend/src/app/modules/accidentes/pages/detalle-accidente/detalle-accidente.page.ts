import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { catchError, of } from 'rxjs';

import { NotificationService } from '../../../../shared/notifications/notification.service';
import { TablerIconComponent } from '../../../../shared/ui/icon/tabler-icon.component';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { AccidenteApiService } from '../../services/accidente-api.service';
import { AccidenteDetalle } from '../../services/models/accidente.types';
import { SEVERIDAD_INFO, SeveridadInfo } from '../../severidad.constants';
import { estadoInfo } from '../../estado.constants';
import { EvidenciaApiService } from '../../../evidencia-unidad/services/evidencia-api.service';
import { EvidenciaFotoItem } from '../../../evidencia-unidad/services/models/evidencia-unidad.types';
import { estadoDespachoLabel, estadoDespachoTono } from '../../../despacho/despacho-tono.constants';
import { DespachoApiService } from '../../../despacho/services/despacho-api.service';
import { IntentoDespacho } from '../../../despacho/services/models/despacho.types';

@Component({
  selector: 'app-detalle-accidente',
  standalone: true,
  imports: [RouterLink, FormsModule, TablerIconComponent, DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './detalle-accidente.page.html',
})
export class DetalleAccidentePage implements OnInit, AfterViewInit {
  private readonly api = inject(AccidenteApiService);
  private readonly evidenciaApi = inject(EvidenciaApiService);
  private readonly despachoApi = inject(DespachoApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly notifications = inject(NotificationService);
  private readonly authApi = inject(AuthApiService);

  @ViewChild('impactoSection') impactoSection?: ElementRef<HTMLElement>;

  readonly accidente = signal<AccidenteDetalle | null>(null);
  readonly loading = signal(false);
  readonly loadError = signal<string | null>(null);
  readonly saving = signal(false);
  /** `true` = modo Editar (`?focus=edit`); `false` = modo Detalles (solo lectura). */
  readonly focusEdit = signal(false);

  numvehiculos = 0;
  numheridos = 0;
  numfallecidos = 0;
  descripcion = '';

  readonly evidencias = signal<EvidenciaFotoItem[]>([]);
  readonly evidenciasError = signal<string | null>(null);
  readonly unidades = signal<IntentoDespacho[]>([]);

  readonly estado = estadoInfo;
  readonly despachoTono = estadoDespachoTono;
  readonly despachoLabel = estadoDespachoLabel;

  ngOnInit(): void {
    const focus = this.route.snapshot.queryParamMap.get('focus');
    this.focusEdit.set(focus === 'edit');
    this.cargar();
  }

  ngAfterViewInit(): void {
    if (this.focusEdit()) {
      queueMicrotask(() => this.scrollToImpacto());
    }
  }

  severidad(idseveridad: number): SeveridadInfo {
    return (
      SEVERIDAD_INFO[idseveridad] ?? {
        value: idseveridad,
        label: `Sev. ${idseveridad}`,
        icon: 'info-circle',
        tone: 'success',
      }
    );
  }

  puedeVerDespacho(): boolean {
    return this.authApi.hasAnyRole(['Operador', 'Despacho', 'Administrador']);
  }

  esModoEditar(): boolean {
    return this.focusEdit();
  }

  tituloModo(): string {
    return this.esModoEditar() ? 'Editar caso' : 'Detalles';
  }

  private idaccidente(): string {
    return this.route.snapshot.paramMap.get('idaccidente') ?? '';
  }

  private scrollToImpacto(): void {
    this.impactoSection?.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const firstInput = this.impactoSection?.nativeElement.querySelector<HTMLElement>(
      'input, textarea',
    );
    firstInput?.focus();
  }

  cargar(): void {
    this.loading.set(true);
    this.loadError.set(null);
    this.api.detalle(this.idaccidente()).subscribe({
      next: (res) => {
        this.accidente.set(res.data);
        this.numvehiculos = res.data.numvehiculos ?? 0;
        this.numheridos = res.data.numheridos ?? 0;
        this.numfallecidos = res.data.numfallecidos ?? 0;
        this.descripcion = res.data.descripcion ?? '';
        this.loading.set(false);
        this.cargarEvidencias();
        if (this.puedeVerDespacho()) {
          this.cargarUnidades();
        }
        if (this.focusEdit()) {
          queueMicrotask(() => this.scrollToImpacto());
        }
      },
      error: () => {
        this.loadError.set('No se pudo cargar el detalle del accidente.');
        this.loading.set(false);
      },
    });
  }

  private cargarEvidencias(): void {
    this.evidenciaApi
      .listarServidor(this.idaccidente(), { limit: 6 })
      .pipe(catchError(() => of(null)))
      .subscribe((res) => {
        if (!res) {
          this.evidenciasError.set('No se pudo cargar la evidencia.');
          return;
        }
        this.evidenciasError.set(null);
        this.evidencias.set(
          res.data.items.filter((item): item is EvidenciaFotoItem => this.evidenciaApi.isFotoItem(item)),
        );
      });
  }

  private cargarUnidades(): void {
    this.despachoApi
      .obtenerEstado(this.idaccidente())
      .pipe(catchError(() => of(null)))
      .subscribe((res) => {
        if (!res) {
          this.unidades.set([]);
          return;
        }
        this.unidades.set(res.data.unidades_activas.length ? res.data.unidades_activas : res.data.intentos);
      });
  }

  guardar(): void {
    if (!this.esModoEditar() || this.saving()) {
      return;
    }
    this.saving.set(true);
    this.api
      .actualizar(this.idaccidente(), {
        numvehiculos: this.numvehiculos,
        numheridos: this.numheridos,
        numfallecidos: this.numfallecidos,
        descripcion: this.descripcion,
      })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.notifications.toast('Actualizado', 'success');
          this.cargar();
        },
        error: (err: HttpErrorResponse) => {
          this.saving.set(false);
          const detail = typeof err.error?.detail === 'string' ? err.error.detail : null;
          this.notifications.alert(detail ?? 'No se pudo guardar el cambio.', 'Error al actualizar');
        },
      });
  }

  descartar(): void {
    const id = this.idaccidente();
    this.api.descartar(id, { motivo: 'Descartado por operador' }).subscribe({
      next: () => {
        this.notifications.toastWithAction('Caso descartado', 'success', 'Deshacer', () => {
          this.api.deshacerDescarte(id).subscribe({
            next: (res) => {
              this.notifications.toast(res.data.message, 'info');
              this.cargar();
            },
            error: () =>
              this.notifications.alert('No se pudo deshacer el descarte.', 'Error al deshacer'),
          });
        });
        this.cargar();
      },
      error: (err: HttpErrorResponse) => {
        const detail = typeof err.error?.detail === 'string' ? err.error.detail : null;
        this.notifications.alert(detail ?? 'No se pudo descartar el caso.', 'Error al descartar');
      },
    });
  }
}
