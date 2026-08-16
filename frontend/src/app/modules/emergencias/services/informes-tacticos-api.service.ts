import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  AbortosPerdidasItem,
  ApiEnvelope,
  ApiEnvelopeCompuesto,
  AsignacionOrigenItem,
  CargaUnidadItem,
  CierresForzadosItem,
  CompletitudItem,
  DescarteFusionItem,
  DistribucionSeveridadItem,
  DistribucionZonaItem,
  ImpactoHumanoItem,
  PeriodoParams,
  RankingUbicacionItem,
  RatioDemandaCapacidadItem,
  RechazoTimeoutItem,
  TiempoAsignadoCerradoItem,
  TiempoReportadoConfirmado,
  TiempoRespuestaSeveridadItem,
  VolumenCasosItem,
} from './models/informes-tacticos.types';

function toQuery(
  periodo: PeriodoParams,
  extra?: Record<string, string | number | undefined>,
): Record<string, string> {
  const query: Record<string, string> = { desde: periodo.desde, hasta: periodo.hasta };
  if (periodo.granularidad) {
    query['granularidad'] = periodo.granularidad;
  }
  if (extra) {
    for (const [k, v] of Object.entries(extra)) {
      if (v !== undefined && v !== null && v !== '') {
        query[k] = String(v);
      }
    }
  }
  return query;
}

@Injectable({ providedIn: 'root' })
export class InformesTacticosApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/informes-tacticos';

  // --- Registro (7) ---
  volumenCasos(p: PeriodoParams): Observable<ApiEnvelope<VolumenCasosItem[]>> {
    return this.http.get<ApiEnvelope<VolumenCasosItem[]>>(`${this.base}/registro/volumen-casos`, {
      params: toQuery(p),
    });
  }

  distribucionSeveridad(p: PeriodoParams): Observable<ApiEnvelope<DistribucionSeveridadItem[]>> {
    return this.http.get<ApiEnvelope<DistribucionSeveridadItem[]>>(
      `${this.base}/registro/distribucion-severidad`,
      { params: toQuery(p) },
    );
  }

  distribucionZona(p: PeriodoParams): Observable<ApiEnvelope<DistribucionZonaItem[]>> {
    return this.http.get<ApiEnvelope<DistribucionZonaItem[]>>(
      `${this.base}/registro/distribucion-zona`,
      { params: toQuery(p) },
    );
  }

  completitudCamposCriticos(p: PeriodoParams): Observable<ApiEnvelope<CompletitudItem[]>> {
    return this.http.get<ApiEnvelope<CompletitudItem[]>>(
      `${this.base}/registro/completitud-campos-criticos`,
      { params: toQuery(p) },
    );
  }

  descarteFusion(p: PeriodoParams): Observable<ApiEnvelope<DescarteFusionItem[]>> {
    return this.http.get<ApiEnvelope<DescarteFusionItem[]>>(`${this.base}/registro/descarte-fusion`, {
      params: toQuery(p),
    });
  }

  rankingUbicaciones(p: PeriodoParams, top = 10): Observable<ApiEnvelope<RankingUbicacionItem[]>> {
    return this.http.get<ApiEnvelope<RankingUbicacionItem[]>>(
      `${this.base}/registro/ranking-ubicaciones`,
      { params: toQuery(p, { top }) },
    );
  }

  impactoHumano(p: PeriodoParams): Observable<ApiEnvelope<ImpactoHumanoItem[]>> {
    return this.http.get<ApiEnvelope<ImpactoHumanoItem[]>>(`${this.base}/registro/impacto-humano`, {
      params: toQuery(p),
    });
  }

  // --- Despacho (6) ---
  asignacionAutomaticaVsManual(
    p: PeriodoParams,
    idcondado?: number,
  ): Observable<ApiEnvelope<AsignacionOrigenItem[]>> {
    return this.http.get<ApiEnvelope<AsignacionOrigenItem[]>>(
      `${this.base}/despacho/asignacion-automatica-vs-manual`,
      { params: toQuery(p, { idcondado }) },
    );
  }

  tiempoReportadoConfirmado(p: PeriodoParams): Observable<ApiEnvelope<TiempoReportadoConfirmado>> {
    return this.http.get<ApiEnvelope<TiempoReportadoConfirmado>>(
      `${this.base}/despacho/tiempo-reportado-confirmado`,
      { params: toQuery(p) },
    );
  }

  tiempoRespuestaPorSeveridad(
    p: PeriodoParams,
    idcondado?: number,
  ): Observable<ApiEnvelope<TiempoRespuestaSeveridadItem[]>> {
    return this.http.get<ApiEnvelope<TiempoRespuestaSeveridadItem[]>>(
      `${this.base}/despacho/tiempo-respuesta-por-severidad`,
      { params: toQuery(p, { idcondado }) },
    );
  }

  rechazoTimeoutPorUnidad(p: PeriodoParams): Observable<ApiEnvelope<RechazoTimeoutItem[]>> {
    return this.http.get<ApiEnvelope<RechazoTimeoutItem[]>>(
      `${this.base}/despacho/rechazo-timeout-por-unidad`,
      { params: toQuery(p) },
    );
  }

  cargaPorUnidad(p: PeriodoParams): Observable<ApiEnvelope<CargaUnidadItem[]>> {
    return this.http.get<ApiEnvelope<CargaUnidadItem[]>>(`${this.base}/despacho/carga-por-unidad`, {
      params: toQuery(p),
    });
  }

  ratioDemandaCapacidad(p: PeriodoParams): Observable<ApiEnvelope<RatioDemandaCapacidadItem[]>> {
    return this.http.get<ApiEnvelope<RatioDemandaCapacidadItem[]>>(
      `${this.base}/despacho/ratio-demanda-capacidad`,
      { params: toQuery(p) },
    );
  }

  // --- Seguimiento (3) ---
  tiempoAsignadoCerrado(p: PeriodoParams): Observable<ApiEnvelope<TiempoAsignadoCerradoItem[]>> {
    return this.http.get<ApiEnvelope<TiempoAsignadoCerradoItem[]>>(
      `${this.base}/seguimiento/tiempo-asignado-cerrado`,
      { params: toQuery(p) },
    );
  }

  cierresForzados(p: PeriodoParams): Observable<ApiEnvelope<CierresForzadosItem[]>> {
    return this.http.get<ApiEnvelope<CierresForzadosItem[]>>(
      `${this.base}/seguimiento/cierres-forzados`,
      { params: toQuery(p) },
    );
  }

  abortosPerdidas(p: PeriodoParams): Observable<ApiEnvelope<AbortosPerdidasItem[]>> {
    return this.http.get<ApiEnvelope<AbortosPerdidasItem[]>>(
      `${this.base}/seguimiento/abortos-perdidas`,
      { params: toQuery(p) },
    );
  }

  // --- Compuestos (3, batch — solo rol Administrador) ---


}
