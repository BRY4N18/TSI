import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { FacturaEnvelope, FacturaListEnvelope } from './models/suscripciones.types';

@Injectable({ providedIn: 'root' })
export class FacturaApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/suscripciones/facturas';

  listar(params?: {
    idcliente?: number;
    cursor?: string;
    limit?: number;
  }): Observable<FacturaListEnvelope> {
    return this.http.get<FacturaListEnvelope>(this.base, { params: params as never });
  }

  obtener(idFactura: string): Observable<FacturaEnvelope> {
    return this.http.get<FacturaEnvelope>(`${this.base}/${idFactura}`);
  }
}
