import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  DespachoCreadoData,
  EstadoDespachoData,
  UnidadesCandidatasData,
} from './models/despacho.types';

@Injectable({ providedIn: 'root' })
export class DespachoApiService {
  private readonly http = inject(HttpClient);

  obtenerEstado(idaccidente: string): Observable<ApiEnvelope<EstadoDespachoData>> {
    return this.http.get<ApiEnvelope<EstadoDespachoData>>(
      `/api/v1/accidentes/${idaccidente}/despacho`,
    );
  }

  listarCandidatas(
    idaccidente: string,
    incluirVecinos = false,
  ): Observable<ApiEnvelope<UnidadesCandidatasData>> {
    const params = new HttpParams().set('incluir_vecinos', String(incluirVecinos));
    return this.http.get<ApiEnvelope<UnidadesCandidatasData>>(
      `/api/v1/accidentes/${idaccidente}/despacho/unidades-candidatas`,
      { params },
    );
  }

  asignarManual(
    idaccidente: string,
    idunidademergencia: number,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<DespachoCreadoData>> {
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.post<ApiEnvelope<DespachoCreadoData>>(
      `/api/v1/accidentes/${idaccidente}/despacho/asignar-manual`,
      { idunidademergencia },
      { headers },
    );
  }

  escalarZona(
    idaccidente: string,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<DespachoCreadoData>> {
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.post<ApiEnvelope<DespachoCreadoData>>(
      `/api/v1/accidentes/${idaccidente}/despacho/escalar-zona`,
      {},
      { headers },
    );
  }

  coordinar(
    idaccidente: string,
    idunidademergencia: number,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<DespachoCreadoData>> {
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.post<ApiEnvelope<DespachoCreadoData>>(
      `/api/v1/accidentes/${idaccidente}/despacho/coordinar`,
      { idunidademergencia },
      { headers },
    );
  }
}
