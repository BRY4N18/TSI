import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ActualizarParametrosRequest,
  ApiEnvelope,
  ParametrosDespachoData,
} from './models/despacho.types';

@Injectable({ providedIn: 'root' })
export class DespachoParametrosApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/despacho/parametros';

  obtener(): Observable<ApiEnvelope<ParametrosDespachoData>> {
    return this.http.get<ApiEnvelope<ParametrosDespachoData>>(this.base);
  }

  actualizar(
    body: ActualizarParametrosRequest,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<ParametrosDespachoData>> {
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.patch<ApiEnvelope<ParametrosDespachoData>>(this.base, body, { headers });
  }
}
