import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Observable } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { InformesTacticosApiService } from '../../services/informes-tacticos-api.service';
import {
  ApiEnvelope,
  ApiEnvelopeCompuesto,
  AsignacionOrigenItem,
  CargaUnidadItem,
  PeriodoParams,
  RatioDemandaCapacidadItem,
  RechazoTimeoutItem,
  TiempoReportadoConfirmado,
  TiempoRespuestaSeveridadItem,
} from '../../services/models/informes-tacticos.types';
import { InformeCardComponent } from '../shared/informe-card.component';
import { PeriodoSelectorComponent } from '../shared/periodo-selector.component';
import { SeveridadBadgeComponent } from '../shared/severidad-badge.component';

interface CardState<T> {
  loading: ReturnType<typeof signal<boolean>>;
  error: ReturnType<typeof signal<string | null>>;
  data: ReturnType<typeof signal<T | null>>;
}

function newState<T>(): CardState<T> {
  return { loading: signal(false), error: signal<string | null>(null), data: signal<T | null>(null) };
}

interface CompuestoState<T> extends CardState<T> {
  materializado: ReturnType<typeof signal<boolean>>;
  ultimaCorrida: ReturnType<typeof signal<string | null>>;
}

function newCompuestoState<T>(): CompuestoState<T> {
  return {
    ...newState<T>(),
    materializado: signal(true),
    ultimaCorrida: signal<string | null>(null),
  };
}

@Component({
  selector: 'app-workpanel-despacho',
  standalone: true,
  imports: [DecimalPipe, FormsModule, InformeCardComponent, PeriodoSelectorComponent, SeveridadBadgeComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './workpanel-despacho.page.html',
})
export class WorkpanelDespachoPage {
  private readonly api = inject(InformesTacticosApiService);
  private readonly authApi = inject(AuthApiService);

  private periodo: PeriodoParams | null = null;
  /** FR-UI-003: solo recorta asignación-origen y tiempo-respuesta-por-severidad. */
  idcondado: number | null = null;

  readonly asignacionOrigen = newState<AsignacionOrigenItem[]>();
  readonly tiempoReportadoConfirmado = newState<TiempoReportadoConfirmado>();
  readonly tiempoRespuestaSeveridad = newState<TiempoRespuestaSeveridadItem[]>();
  readonly rechazoTimeout = newState<RechazoTimeoutItem[]>();
  readonly cargaPorUnidad = newState<CargaUnidadItem[]>();
  readonly ratioDemandaCapacidad = newState<RatioDemandaCapacidadItem[]>();

  /** FR-UI-003: tarjeta compuesta (batch), visible solo para el rol Administrador (Supervisor). */
  readonly puedeVerCompuestos = this.authApi.hasRole('Administrador');

  onPeriodoChange(periodo: PeriodoParams): void {
    this.periodo = periodo;
    this.cargarTodo();
  }

  onCondadoChange(): void {
    if (!this.periodo) {
      return;
    }
    this.cargar(
      this.asignacionOrigen,
      this.api.asignacionAutomaticaVsManual(this.periodo, this.idcondado ?? undefined),
    );
    this.cargar(
      this.tiempoRespuestaSeveridad,
      this.api.tiempoRespuestaPorSeveridad(this.periodo, this.idcondado ?? undefined),
    );
  }

  cargarTodo(): void {
    if (!this.periodo) {
      return;
    }
    this.cargar(
      this.asignacionOrigen,
      this.api.asignacionAutomaticaVsManual(this.periodo, this.idcondado ?? undefined),
    );
    this.cargar(this.tiempoReportadoConfirmado, this.api.tiempoReportadoConfirmado(this.periodo));
    this.cargar(
      this.tiempoRespuestaSeveridad,
      this.api.tiempoRespuestaPorSeveridad(this.periodo, this.idcondado ?? undefined),
    );
    this.cargar(this.rechazoTimeout, this.api.rechazoTimeoutPorUnidad(this.periodo));
    this.cargar(this.cargaPorUnidad, this.api.cargaPorUnidad(this.periodo));
    this.cargar(this.ratioDemandaCapacidad, this.api.ratioDemandaCapacidad(this.periodo));
    if (this.puedeVerCompuestos) {
    }
  }

  private cargar<T>(state: CardState<T>, obs: Observable<ApiEnvelope<T>>): void {
    state.loading.set(true);
    state.error.set(null);
    obs.subscribe({
      next: (res) => {
        state.data.set(res.data);
        state.loading.set(false);
      },
      error: () => {
        state.loading.set(false);
        state.error.set('No se pudo cargar este informe.');
      },
    });
  }

  private cargarCompuesto<T>(state: CompuestoState<T>, obs: Observable<ApiEnvelopeCompuesto<T>>): void {
    state.loading.set(true);
    state.error.set(null);
    obs.subscribe({
      next: (res) => {
        state.data.set(res.data);
        state.materializado.set(res.meta.materializado);
        state.ultimaCorrida.set(res.meta.ultima_corrida);
        state.loading.set(false);
      },
      error: () => {
        state.loading.set(false);
        state.error.set('No se pudo cargar este informe.');
      },
    });
  }
}
