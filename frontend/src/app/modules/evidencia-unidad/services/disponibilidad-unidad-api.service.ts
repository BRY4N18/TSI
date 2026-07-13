import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  DeclararEstadoDisponibilidadRequest,
  DisponibilidadUnidadData,
  EstadoDisponibilidadUnidad,
  HistorialEstadoUnidadData,
  HistorialEstadoUnidadItem,
  UnidadEmergenciaResumen,
} from './models/evidencia-unidad.types';

@Injectable({ providedIn: 'root' })
export class DisponibilidadUnidadApiService {
  private readonly http = inject(HttpClient);
  private readonly miUnidadBase = '/api/v1/mi-unidad-emergencia/disponibilidad';
  private readonly unidadesBase = '/api/v1/unidades-emergencia';

  consultarMiDisponibilidad(): Observable<ApiEnvelope<DisponibilidadUnidadData>> {
    return this.http.get<ApiEnvelope<DisponibilidadUnidadData>>(this.miUnidadBase);
  }

  declararMiEstado(
    body: DeclararEstadoDisponibilidadRequest,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<HistorialEstadoUnidadData>> {
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.post<ApiEnvelope<HistorialEstadoUnidadData>>(this.miUnidadBase, body, {
      headers,
    });
  }

  listarUnidades(params?: {
    estado?: EstadoDisponibilidadUnidad;
    idtipounidad?: number;
    cursor?: string;
    limit?: number;
  }): Observable<ApiEnvelope<{ items: UnidadEmergenciaResumen[] }>> {
    let httpParams = new HttpParams();
    if (params?.estado) {
      httpParams = httpParams.set('estado', params.estado);
    }
    if (params?.idtipounidad != null) {
      httpParams = httpParams.set('idtipounidad', String(params.idtipounidad));
    }
    if (params?.cursor) {
      httpParams = httpParams.set('cursor', params.cursor);
    }
    if (params?.limit != null) {
      httpParams = httpParams.set('limit', String(params.limit));
    }
    return this.http.get<ApiEnvelope<{ items: UnidadEmergenciaResumen[] }>>(this.unidadesBase, {
      params: httpParams,
    });
  }

  consultarDisponibilidad(
    idunidademergencia: number,
  ): Observable<ApiEnvelope<DisponibilidadUnidadData>> {
    return this.http.get<ApiEnvelope<DisponibilidadUnidadData>>(
      `${this.unidadesBase}/${idunidademergencia}/disponibilidad`,
    );
  }

  consultarHistorial(
    idunidademergencia: number,
    params?: { cursor?: string; limit?: number },
  ): Observable<ApiEnvelope<{ items: HistorialEstadoUnidadItem[] }>> {
    let httpParams = new HttpParams();
    if (params?.cursor) {
      httpParams = httpParams.set('cursor', params.cursor);
    }
    if (params?.limit != null) {
      httpParams = httpParams.set('limit', String(params.limit));
    }
    return this.http.get<ApiEnvelope<{ items: HistorialEstadoUnidadItem[] }>>(
      `${this.unidadesBase}/${idunidademergencia}/historial-estado`,
      { params: httpParams },
    );
  }

  declararEstado(
    idunidademergencia: number,
    body: DeclararEstadoDisponibilidadRequest,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<HistorialEstadoUnidadData>> {
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.post<ApiEnvelope<HistorialEstadoUnidadData>>(
      `${this.unidadesBase}/${idunidademergencia}/disponibilidad`,
      body,
      { headers },
    );
  }
}
