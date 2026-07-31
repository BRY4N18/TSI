import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { switchMap } from 'rxjs/operators';

import {
  Plan,
  PlanEnvelope,
  PlanListEnvelope,
  PlanListQuery,
  PlanPatchRequest,
  PlanRequest,
} from './models/suscripciones.types';

@Injectable({ providedIn: 'root' })
export class PlanApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/suscripciones/planes';

  /**
   * Listado paginado. Preferir `PlanListQuery` con `limit` (default 20).
   * El overload `boolean` queda solo para compat residual (mapea a solo_activos + limit 100).
   */
  listar(params: boolean | PlanListQuery = true): Observable<PlanListEnvelope> {
    let httpParams = new HttpParams();
    if (typeof params === 'boolean') {
      httpParams = httpParams.set('limit', '100').set('solo_activos', String(params));
    } else {
      const limit = params.limit ?? 20;
      httpParams = httpParams.set('limit', String(limit));
      if (params.cursor != null) {
        httpParams = httpParams.set('cursor', String(params.cursor));
      }
      if (params.q) {
        httpParams = httpParams.set('q', params.q);
      }
      if (params.activo !== undefined) {
        httpParams = httpParams.set('activo', String(params.activo));
      } else if (params.solo_activos !== undefined) {
        httpParams = httpParams.set('solo_activos', String(params.solo_activos));
      }
      if (params.nivel) {
        httpParams = httpParams.set('nivel', params.nivel);
      }
    }
    return this.http.get<PlanListEnvelope>(this.base, { params: httpParams });
  }

  /**
   * Lectura puntual sin GET /planes/{id}: recorre páginas acotadas (limit 100)
   * hasta encontrar el id o agotar next_cursor — no materializa el catálogo en el caller.
   */
  buscarPorId(idplan: number): Observable<Plan | null> {
    const fetchPage = (cursor: number | null): Observable<Plan | null> =>
      this.listar({ cursor, limit: 100, solo_activos: false }).pipe(
        switchMap((res) => {
          const found = (res.data ?? []).find((p) => p.idplan === idplan) ?? null;
          if (found) {
            return of(found);
          }
          const raw = res.meta?.pagination?.next_cursor;
          if (raw == null || raw === '') {
            return of(null);
          }
          const next = typeof raw === 'string' ? Number(raw) : raw;
          if (!Number.isFinite(next)) {
            return of(null);
          }
          return fetchPage(next);
        }),
      );
    return fetchPage(null);
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
