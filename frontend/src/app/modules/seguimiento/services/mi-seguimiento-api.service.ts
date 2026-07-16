import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  AbortarMisionData,
  AbortarMisionRequest,
  ApiEnvelope,
  LlegadaRegistradaData,
  MiSeguimientoActualData,
  PosicionAceptadaData,
  RegistrarPosicionRequest,
} from '../models/seguimiento.types';

@Injectable({ providedIn: 'root' })
export class MiSeguimientoApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/mi-seguimiento';

  obtenerActual(): Observable<ApiEnvelope<MiSeguimientoActualData>> {
    return this.http.get<ApiEnvelope<MiSeguimientoActualData>>(`${this.baseUrl}/actual`);
  }

  registrarPosicion(
    body: RegistrarPosicionRequest,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<PosicionAceptadaData>> {
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.post<ApiEnvelope<PosicionAceptadaData>>(`${this.baseUrl}/posicion`, body, {
      headers,
    });
  }

  registrarLlegada(
    iddespacho: number,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<LlegadaRegistradaData>> {
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.post<ApiEnvelope<LlegadaRegistradaData>>(
      `${this.baseUrl}/despachos/${iddespacho}/llegada`,
      {},
      { headers },
    );
  }

  abortarMision(
    iddespacho: number,
    body?: AbortarMisionRequest,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<AbortarMisionData>> {
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.post<ApiEnvelope<AbortarMisionData>>(
      `${this.baseUrl}/despachos/${iddespacho}/abortar`,
      body ?? {},
      { headers },
    );
  }
}
