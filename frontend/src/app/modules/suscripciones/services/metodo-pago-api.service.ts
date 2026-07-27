import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  MetodoPagoEnvelope,
  MetodoPagoListEnvelope,
  MetodoPagoRequest,
} from './models/suscripciones.types';

@Injectable({ providedIn: 'root' })
export class MetodoPagoApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/suscripciones/metodos-pago';

  listar(): Observable<MetodoPagoListEnvelope> {
    return this.http.get<MetodoPagoListEnvelope>(this.base);
  }

  registrar(body: MetodoPagoRequest, idempotencyKey: string): Observable<MetodoPagoEnvelope> {
    const headers = new HttpHeaders({ 'Idempotency-Key': idempotencyKey });
    return this.http.post<MetodoPagoEnvelope>(this.base, body, { headers });
  }
}
