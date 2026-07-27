import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  PlanEnvelope,
  PlanListEnvelope,
  PlanPatchRequest,
  PlanRequest,
} from './models/suscripciones.types';

@Injectable({ providedIn: 'root' })
export class PlanApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/suscripciones/planes';

  listar(soloActivos = true): Observable<PlanListEnvelope> {
    return this.http.get<PlanListEnvelope>(this.base, {
      params: { solo_activos: soloActivos },
    });
  }

  crear(body: PlanRequest, idempotencyKey: string): Observable<PlanEnvelope> {
    const headers = new HttpHeaders({ 'Idempotency-Key': idempotencyKey });
    return this.http.post<PlanEnvelope>(this.base, body, { headers });
  }

  actualizar(
    idplan: number,
    body: PlanPatchRequest,
    idempotencyKey: string,
  ): Observable<PlanEnvelope> {
    const headers = new HttpHeaders({ 'Idempotency-Key': idempotencyKey });
    return this.http.patch<PlanEnvelope>(`${this.base}/${idplan}`, body, { headers });
  }
}
