import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  ConfirmarDespachoData,
  DetalleDespachoUnidadData,
  PendienteDespacho,
  RechazarDespachoData,
  RechazarDespachoRequest,
} from './models/despacho.types';

@Injectable({ providedIn: 'root' })
export class MiDespachoApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/mi-despacho';

  listarPendientes(): Observable<ApiEnvelope<{ pendientes: PendienteDespacho[] }>> {
    return this.http.get<ApiEnvelope<{ pendientes: PendienteDespacho[] }>>(
      `${this.base}/pendientes`,
    );
  }

  obtenerDetalle(
    idnotificaciondespacho: number,
  ): Observable<ApiEnvelope<DetalleDespachoUnidadData>> {
    return this.http.get<ApiEnvelope<DetalleDespachoUnidadData>>(
      `${this.base}/${idnotificaciondespacho}`,
    );
  }

  confirmar(
    idnotificaciondespacho: number,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<ConfirmarDespachoData>> {
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.post<ApiEnvelope<ConfirmarDespachoData>>(
      `${this.base}/${idnotificaciondespacho}/confirmar`,
      {},
      { headers },
    );
  }

  rechazar(
    idnotificaciondespacho: number,
    body: RechazarDespachoRequest,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<RechazarDespachoData>> {
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.post<ApiEnvelope<RechazarDespachoData>>(
      `${this.base}/${idnotificaciondespacho}/rechazar`,
      body,
      { headers },
    );
  }
}
