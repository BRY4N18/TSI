import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Observable } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { InformesTacticosApiService } from '../../services/informes-tacticos-api.service';
import {
  AbortosPerdidasItem,
  ApiEnvelope,
  ApiEnvelopeCompuesto,
  CierresForzadosItem,
  PeriodoParams,
  TiempoAsignadoCerradoItem,
} from '../../services/models/informes-tacticos.types';
import { InformeCardComponent } from '../shared/informe-card.component';
import { PeriodoSelectorComponent } from '../shared/periodo-selector.component';
import { SerieItem, TimeseriesChartComponent } from '../shared/timeseries-chart.component';

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
  selector: 'app-workpanel-seguimiento',
  standalone: true,
  imports: [DecimalPipe, InformeCardComponent, PeriodoSelectorComponent, TimeseriesChartComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './workpanel-seguimiento.page.html',
})
export class WorkpanelSeguimientoPage {
  private readonly api = inject(InformesTacticosApiService);
  private readonly authApi = inject(AuthApiService);

  private periodo: PeriodoParams | null = null;

  readonly tiempoAsignadoCerrado = newState<TiempoAsignadoCerradoItem[]>();
  readonly cierresForzados = newState<CierresForzadosItem[]>();
  readonly abortosPerdidas = newState<AbortosPerdidasItem[]>();

  /** FR-UI-003: tarjeta compuesta (batch), visible solo para el rol Administrador (Supervisor). */
  readonly puedeVerCompuestos = this.authApi.hasRole('Administrador');

  serieCierresForzados(): SerieItem[] {
    return (this.cierresForzados.data() ?? []).map((d) => ({
      periodo: d.periodo,
      valor: d.pct_cierres_forzados * 100,
    }));
  }

  onPeriodoChange(periodo: PeriodoParams): void {
    this.periodo = periodo;
    this.cargarTodo();
  }

  cargarTodo(): void {
    if (!this.periodo) {
      return;
    }
    this.cargar(this.tiempoAsignadoCerrado, this.api.tiempoAsignadoCerrado(this.periodo));
    this.cargar(this.cierresForzados, this.api.cierresForzados(this.periodo));
    this.cargar(this.abortosPerdidas, this.api.abortosPerdidas(this.periodo));
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
