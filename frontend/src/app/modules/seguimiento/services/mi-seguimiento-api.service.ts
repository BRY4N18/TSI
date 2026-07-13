import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  AbortarMisionData,
  AbortarMisionRequest,
  ApiEnvelope,
  LlegadaRegistradaData,
  PosicionAceptadaData,
  RegistrarPosicionRequest,
} from '../models/seguimiento.types';

@Injectable({ providedIn: 'root' })
export class MiSeguimientoApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/mi-seguimiento';

  registrarPosicion(body: RegistrarPosicionRequest): Observable<ApiEnvelope<PosicionAceptadaData>> {
    return this.http.post<ApiEnvelope<PosicionAceptadaData>>(`${this.baseUrl}/posicion`, body);
  }

  registrarLlegada(iddespacho: number): Observable<ApiEnvelope<LlegadaRegistradaData>> {
    return this.http.post<ApiEnvelope<LlegadaRegistradaData>>(
      `${this.baseUrl}/despachos/${iddespacho}/llegada`,
      {},
    );
  }

  abortarMision(
    iddespacho: number,
    body?: AbortarMisionRequest,
  ): Observable<ApiEnvelope<AbortarMisionData>> {
    return this.http.post<ApiEnvelope<AbortarMisionData>>(
      `${this.baseUrl}/despachos/${iddespacho}/abortar`,
      body ?? {},
    );
  }
}
