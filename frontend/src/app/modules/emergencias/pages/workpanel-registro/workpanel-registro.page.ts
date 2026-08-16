import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Observable } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { InformesTacticosApiService } from '../../services/informes-tacticos-api.service';
import {
  ApiEnvelope,
  ApiEnvelopeCompuesto,
  CompletitudItem,
  DescarteFusionItem,
  DistribucionSeveridadItem,
  DistribucionZonaItem,
  ImpactoHumanoItem,
  PeriodoParams,
  RankingUbicacionItem,
  VolumenCasosItem,
} from '../../services/models/informes-tacticos.types';
import { InformeCardComponent } from '../shared/informe-card.component';
import { PeriodoSelectorComponent } from '../shared/periodo-selector.component';
import { DualSerieItem, DualTimeseriesChartComponent } from '../shared/dual-timeseries-chart.component';
import { SeveridadBadgeComponent } from '../shared/severidad-badge.component';
import { SerieItem, TimeseriesChartComponent } from '../shared/timeseries-chart.component';
import {
  SerieMultiConfig,
  SerieMultiItem,
  TimeseriesMultiChartComponent,
} from '../shared/timeseries-multi-chart.component';

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
  selector: 'app-workpanel-registro',
  standalone: true,
  imports: [
    DecimalPipe,
    InformeCardComponent,
    PeriodoSelectorComponent,
    SeveridadBadgeComponent,
    TimeseriesChartComponent,
    DualTimeseriesChartComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './workpanel-registro.page.html',
})
export class WorkpanelRegistroPage {
  private readonly api = inject(InformesTacticosApiService);
  private readonly authApi = inject(AuthApiService);

  private periodo: PeriodoParams | null = null;

  readonly volumenCasos = newState<VolumenCasosItem[]>();
  readonly distribucionSeveridad = newState<DistribucionSeveridadItem[]>();
  readonly distribucionZona = newState<DistribucionZonaItem[]>();
  readonly completitud = newState<CompletitudItem[]>();
  readonly descarteFusion = newState<DescarteFusionItem[]>();
  readonly ranking = newState<RankingUbicacionItem[]>();
  readonly impactoHumano = newState<ImpactoHumanoItem[]>();

  /** FR-UI-003: tarjeta compuesta (batch), visible solo para el rol Administrador (Supervisor). */
  readonly puedeVerCompuestos = this.authApi.hasRole('Administrador');

  serieVolumenCasos(): SerieItem[] {
    return (this.volumenCasos.data() ?? []).map((d) => ({ periodo: d.periodo, valor: d.total_casos }));
  }

  serieCompletitud(): SerieItem[] {
    return (this.completitud.data() ?? []).map((d) => ({ periodo: d.periodo, valor: d.pct_completos * 100 }));
  }

  serieDescarteFusion(): DualSerieItem[] {
    return (this.descarteFusion.data() ?? []).map((d) => ({
      periodo: d.periodo,
      a: d.pct_descarte * 100,
      b: d.pct_fusion * 100,
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
    this.cargar(this.volumenCasos, this.api.volumenCasos(this.periodo));
    this.cargar(this.distribucionSeveridad, this.api.distribucionSeveridad(this.periodo));
    this.cargar(this.distribucionZona, this.api.distribucionZona(this.periodo));
    this.cargar(this.completitud, this.api.completitudCamposCriticos(this.periodo));
    this.cargar(this.descarteFusion, this.api.descarteFusion(this.periodo));
    this.cargar(this.ranking, this.api.rankingUbicaciones(this.periodo));
    this.cargar(this.impactoHumano, this.api.impactoHumano(this.periodo));
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
