import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  Cliente,
  ConversionRequest,
  EntradaDirectaRequest,
  Prospecto,
} from '../models/prospectos.types';

@Injectable({ providedIn: 'root' })
export class ConversionApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/ventas-crm';

  convertir(
    idprospecto: number,
    body: ConversionRequest,
    idempotencyKey: string,
  ): Observable<ApiEnvelope<{ prospecto: Prospecto; cliente: Cliente }>> {
    const headers = new HttpHeaders({ 'Idempotency-Key': idempotencyKey });
    return this.http.post<ApiEnvelope<{ prospecto: Prospecto; cliente: Cliente }>>(
      `${this.base}/prospectos/${idprospecto}/conversion`,
      body,
      { headers },
    );
  }

  entradaDirecta(body: EntradaDirectaRequest): Observable<ApiEnvelope<Cliente>> {
    return this.http.post<ApiEnvelope<Cliente>>(`${this.base}/clientes/entrada-directa`, body);
  }
}
