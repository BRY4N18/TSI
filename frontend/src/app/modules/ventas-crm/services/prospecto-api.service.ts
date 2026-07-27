import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  AsignacionManualRequest,
  Prospecto,
  RegistroProspectoRequest,
} from '../models/prospectos.types';

@Injectable({ providedIn: 'root' })
export class ProspectoApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/ventas-crm/prospectos';

  registrar(body: RegistroProspectoRequest): Observable<ApiEnvelope<Prospecto>> {
    return this.http.post<ApiEnvelope<Prospecto>>(this.base, body);
  }

  listar(params?: {
    cursor?: string;
    limit?: number;
    activo?: boolean;
    etapa_actual?: string;
  }): Observable<ApiEnvelope<Prospecto[]>> {
    return this.http.get<ApiEnvelope<Prospecto[]>>(this.base, { params: params as never });
  }

  obtener(idprospecto: number): Observable<ApiEnvelope<Prospecto>> {
    return this.http.get<ApiEnvelope<Prospecto>>(`${this.base}/${idprospecto}`);
  }

  asignar(
    idprospecto: number,
    body: AsignacionManualRequest,
  ): Observable<ApiEnvelope<{ prospecto: Prospecto }>> {
    return this.http.patch<ApiEnvelope<{ prospecto: Prospecto }>>(
      `${this.base}/${idprospecto}/asignacion`,
      body,
    );
  }
}
