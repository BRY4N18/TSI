import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  RechazoDefinitivoData,
  RegionEstadoData,
  ValidacionHistorialItem,
  ValidacionRegionData,
  ValidacionRegionRequest,
} from '../models/region-operativa.contract';

@Injectable({ providedIn: 'root' })
export class RegionOperativaApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/red-operativa/regiones';

  ejecutarValidacion(
    body: ValidacionRegionRequest,
  ): Observable<ApiEnvelope<ValidacionRegionData>> {
    return this.http.post<ApiEnvelope<ValidacionRegionData>>(`${this.baseUrl}/validaciones`, body);
  }

  listarHistorialValidacion(
    idregionoperativa: number,
  ): Observable<ApiEnvelope<ValidacionHistorialItem[]>> {
    return this.http.get<ApiEnvelope<ValidacionHistorialItem[]>>(
      `${this.baseUrl}/${idregionoperativa}/validaciones`,
    );
  }

  rechazarDefinitivamente(
    idregionoperativa: number,
  ): Observable<ApiEnvelope<RechazoDefinitivoData>> {
    return this.http.post<ApiEnvelope<RechazoDefinitivoData>>(
      `${this.baseUrl}/${idregionoperativa}/rechazo-definitivo`,
      {},
    );
  }

  reevaluarRegion(
    idregionoperativa: number,
    estadoregion: 'En_Alerta' | 'Despublicada',
    motivo: string,
  ): Observable<ApiEnvelope<RegionEstadoData>> {
    return this.http.post<ApiEnvelope<RegionEstadoData>>(
      `${this.baseUrl}/${idregionoperativa}/reevaluacion`,
      { estadoregion, motivo },
    );
  }

  despublicarAutomaticamente(
    idregionoperativa: number,
  ): Observable<ApiEnvelope<RegionEstadoData>> {
    return this.http.post<ApiEnvelope<RegionEstadoData>>(
      `${this.baseUrl}/${idregionoperativa}/despublicacion-automatica`,
      {},
    );
  }

  listar(params?: {
    cursor?: number;
    limit?: number;
    estadoregion?: string;
  }): Observable<ApiEnvelope<{ items: RegionEstadoData[] }>> {
    const q = new URLSearchParams();
    if (params?.cursor != null) q.set('cursor', String(params.cursor));
    if (params?.limit != null) q.set('limit', String(params.limit));
    if (params?.estadoregion) q.set('estadoregion', params.estadoregion);
    const qs = q.toString();
    return this.http.get<ApiEnvelope<{ items: RegionEstadoData[] }>>(
      `${this.baseUrl}${qs ? `?${qs}` : ''}`,
    );
  }

  obtener(idregionoperativa: number): Observable<ApiEnvelope<RegionEstadoData>> {
    return this.http.get<ApiEnvelope<RegionEstadoData>>(`${this.baseUrl}/${idregionoperativa}`);
  }
}
