import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiEnvelope, ExpedienteData, HistorialEmergenciasData } from '../models/seguimiento.types';

@Injectable({ providedIn: 'root' })
export class ExpedienteClienteApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/cliente/expedientes';

  listar(params?: { cursor?: string; limit?: number }): Observable<ApiEnvelope<HistorialEmergenciasData>> {
    let httpParams = new HttpParams();
    if (params?.cursor) {
      httpParams = httpParams.set('cursor', params.cursor);
    }
    if (params?.limit != null) {
      httpParams = httpParams.set('limit', String(params.limit));
    }
    return this.http.get<ApiEnvelope<HistorialEmergenciasData>>(this.baseUrl, { params: httpParams });
  }

  obtenerDetalle(idaccidente: string): Observable<ApiEnvelope<ExpedienteData>> {
    return this.http.get<ApiEnvelope<ExpedienteData>>(`${this.baseUrl}/${idaccidente}`);
  }

  descargarPdf(idaccidente: string): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/${idaccidente}/pdf`, { responseType: 'blob' });
  }
}
