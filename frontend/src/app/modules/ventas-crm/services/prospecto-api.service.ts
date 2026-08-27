import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  AsignacionManualRequest,
  AsignacionProspecto,
  Prospecto,
  ProspectoDetalle,
  ProspectoListQuery,
  RegistroProspectoRequest,
} from '../models/prospectos.types';

@Injectable({ providedIn: 'root' })
export class ProspectoApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/ventas-crm/prospectos';

  registrar(body: RegistroProspectoRequest): Observable<ApiEnvelope<Prospecto>> {
    return this.http.post<ApiEnvelope<Prospecto>>(this.base, body);
  }

  listar(params: ProspectoListQuery = {}): Observable<ApiEnvelope<Prospecto[]>> {
    let httpParams = new HttpParams();
    const limit = params.limit ?? 20;
    httpParams = httpParams.set('limit', String(limit));
    if (params.cursor != null && params.cursor !== '') {
      httpParams = httpParams.set('cursor', String(params.cursor));
    }
    if (params.activo !== undefined) {
      httpParams = httpParams.set('activo', String(params.activo));
    }
    if (params.etapa_actual) {
      httpParams = httpParams.set('etapa_actual', params.etapa_actual);
    }
    return this.http.get<ApiEnvelope<Prospecto[]>>(this.base, { params: httpParams });
  }

  /** Devuelve el prospecto **con sus dos historiales** (RF-CPP-008). */
  obtener(idprospecto: number): Observable<ApiEnvelope<ProspectoDetalle>> {
    return this.http.get<ApiEnvelope<ProspectoDetalle>>(`${this.base}/${idprospecto}`);
  }

  asignar(
    idprospecto: number,
    body: AsignacionManualRequest,
  ): Observable<ApiEnvelope<{ prospecto: Prospecto; asignacion: AsignacionProspecto }>> {
    return this.http.patch<
      ApiEnvelope<{ prospecto: Prospecto; asignacion: AsignacionProspecto }>
    >(
      `${this.base}/${idprospecto}/asignacion`,
      body,
    );
  }
}
