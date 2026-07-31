import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  BajaUnidadData,
  CatalogQueryState,
  ImportacionLoteData,
  UnidadCreateRequest,
  UnidadCreatedData,
  UnidadEmergenciaData,
  UnidadInvitacionReenvioData,
  UnidadPatchRequest,
  UnidadUpdatedData,
  UnidadesListData,
} from '../models/unidad-emergencia.contract';

@Injectable({ providedIn: 'root' })
export class UnidadEmergenciaApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/red-operativa/unidades';

  registrar(body: UnidadCreateRequest): Observable<ApiEnvelope<UnidadCreatedData>> {
    return this.http.post<ApiEnvelope<UnidadCreatedData>>(this.baseUrl, body);
  }

  obtener(idunidademergencia: number): Observable<ApiEnvelope<UnidadEmergenciaData>> {
    return this.http.get<ApiEnvelope<UnidadEmergenciaData>>(
      `${this.baseUrl}/${idunidademergencia}`,
    );
  }

  editar(
    idunidademergencia: number,
    body: UnidadPatchRequest,
    confirmarEdicionCritica = false,
  ): Observable<ApiEnvelope<UnidadUpdatedData>> {
    const params = confirmarEdicionCritica ? '?confirmar_edicion_critica=true' : '';
    return this.http.patch<ApiEnvelope<UnidadUpdatedData>>(
      `${this.baseUrl}/${idunidademergencia}${params}`,
      body,
    );
  }

  importarLote(archivo: File): Observable<ApiEnvelope<ImportacionLoteData>> {
    const formData = new FormData();
    formData.append('archivo', archivo);
    return this.http.post<ApiEnvelope<ImportacionLoteData>>(
      `${this.baseUrl}/importacion-lote`,
      formData,
    );
  }

  darDeBaja(
    idunidademergencia: number,
    motivo: string,
    forzar = false,
  ): Observable<ApiEnvelope<BajaUnidadData>> {
    return this.http.post<ApiEnvelope<BajaUnidadData>>(
      `${this.baseUrl}/${idunidademergencia}/baja`,
      { motivo, forzar },
    );
  }

  reactivar(idunidademergencia: number): Observable<ApiEnvelope<UnidadEmergenciaData>> {
    return this.http.post<ApiEnvelope<UnidadEmergenciaData>>(
      `${this.baseUrl}/${idunidademergencia}/reactivar`,
      {},
    );
  }

  reenviarInvitacion(
    idunidademergencia: number,
  ): Observable<ApiEnvelope<UnidadInvitacionReenvioData>> {
    return this.http.post<ApiEnvelope<UnidadInvitacionReenvioData>>(
      `${this.baseUrl}/${idunidademergencia}/invitacion/reenviar`,
      {},
    );
  }

  listar(query?: CatalogQueryState): Observable<ApiEnvelope<UnidadesListData>> {
    let params = new HttpParams();
    const limit = query?.limit ?? 20;
    params = params.set('limit', String(limit));
    if (query?.cursor != null && query.cursor > 0) {
      params = params.set('cursor', String(query.cursor));
    }
    const q = query?.q?.trim();
    if (q) {
      params = params.set('q', q);
    }
    if (query?.activo === true || query?.activo === false) {
      params = params.set('activo', String(query.activo));
    }
    const tipo = query?.tipounidademergencia;
    if (tipo) {
      params = params.set('tipounidademergencia', tipo);
    }
    return this.http.get<ApiEnvelope<UnidadesListData>>(this.baseUrl, { params });
  }
}
