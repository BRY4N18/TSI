import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  CerrarCasoRequest,
  CierreCasoData,
  CancelarCasoRequest,
  ExpedienteData,
  ForzarRetiroData,
  HistorialEmergenciasData,
  MapaSeguimientoData,
  SeguimientoAccidenteData,
} from '../models/seguimiento.types';

@Injectable({ providedIn: 'root' })
export class SeguimientoApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1';

  obtenerMapa(): Observable<ApiEnvelope<MapaSeguimientoData>> {
    return this.http.get<ApiEnvelope<MapaSeguimientoData>>(`${this.baseUrl}/seguimiento/mapa`);
  }

  obtenerSeguimientoAccidente(idaccidente: string): Observable<ApiEnvelope<SeguimientoAccidenteData>> {
    return this.http.get<ApiEnvelope<SeguimientoAccidenteData>>(
      `${this.baseUrl}/accidentes/${idaccidente}/seguimiento`,
    );
  }

  listarHistorial(params?: {
    cursor?: string;
    limit?: number;
    estado?: string;
    idseveridad?: number;
    idunidademergencia?: number;
    fechaDesde?: number;
    fechaHasta?: number;
    idciudad?: number;
    idestadoregion?: number;
  }): Observable<ApiEnvelope<HistorialEmergenciasData>> {
    let httpParams = new HttpParams();
    if (params?.cursor) {
      httpParams = httpParams.set('cursor', params.cursor);
    }
    if (params?.limit != null) {
      httpParams = httpParams.set('limit', String(params.limit));
    }
    if (params?.estado) {
      httpParams = httpParams.set('estado', params.estado);
    }
    if (params?.idseveridad != null) {
      httpParams = httpParams.set('idseveridad', String(params.idseveridad));
    }
    if (params?.idunidademergencia != null) {
      httpParams = httpParams.set('idunidademergencia', String(params.idunidademergencia));
    }
    if (params?.fechaDesde != null) {
      httpParams = httpParams.set('fecha_desde', String(params.fechaDesde));
    }
    if (params?.fechaHasta != null) {
      httpParams = httpParams.set('fecha_hasta', String(params.fechaHasta));
    }
    if (params?.idciudad != null) {
      httpParams = httpParams.set('idciudad', String(params.idciudad));
    }
    if (params?.idestadoregion != null) {
      httpParams = httpParams.set('idestadoregion', String(params.idestadoregion));
    }
    return this.http.get<ApiEnvelope<HistorialEmergenciasData>>(
      `${this.baseUrl}/emergencias/historial`,
      { params: httpParams },
    );
  }

  obtenerExpedienteOperador(idaccidente: string): Observable<ApiEnvelope<ExpedienteData>> {
    return this.http.get<ApiEnvelope<ExpedienteData>>(
      `${this.baseUrl}/emergencias/historial/${idaccidente}/expediente`,
    );
  }

  cerrarCaso(idaccidente: string, body: CerrarCasoRequest): Observable<ApiEnvelope<CierreCasoData>> {
    return this.http.post<ApiEnvelope<CierreCasoData>>(
      `${this.baseUrl}/accidentes/${idaccidente}/cerrar`,
      body,
    );
  }

  cancelarCaso(idaccidente: string, body: CancelarCasoRequest): Observable<ApiEnvelope<CierreCasoData>> {
    return this.http.post<ApiEnvelope<CierreCasoData>>(
      `${this.baseUrl}/accidentes/${idaccidente}/cancelar`,
      body,
    );
  }

  forzarRetiro(iddespacho: number): Observable<ApiEnvelope<ForzarRetiroData>> {
    return this.http.post<ApiEnvelope<ForzarRetiroData>>(
      `${this.baseUrl}/despachos/${iddespacho}/forzar-retiro`,
      {},
    );
  }
}
