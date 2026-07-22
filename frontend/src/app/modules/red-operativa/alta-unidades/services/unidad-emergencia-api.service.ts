import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  BajaUnidadData,
  DisponibilidadData,
  ImportacionLoteData,
  UnidadCreateRequest,
  UnidadCreatedData,
  UnidadEmergenciaData,
  UnidadPatchRequest,
  UnidadUpdatedData,
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

  declararDisponibilidad(
    idunidademergencia: number,
    estadonuevo: string,
  ): Observable<ApiEnvelope<DisponibilidadData>> {
    return this.http.post<ApiEnvelope<DisponibilidadData>>(
      `${this.baseUrl}/${idunidademergencia}/disponibilidad`,
      { estadonuevo },
    );
  }
}
