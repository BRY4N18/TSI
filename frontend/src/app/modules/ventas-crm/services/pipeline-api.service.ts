import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  PipelineTransicionRequest,
  Prospecto,
  TransicionPipeline,
} from '../models/prospectos.types';

@Injectable({ providedIn: 'root' })
export class PipelineApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/ventas-crm/prospectos';

  registrarTransicion(
    idprospecto: number,
    body: PipelineTransicionRequest,
    // El backend devuelve también la fila de `Fact_Pipeline` recién creada; la
    // pantalla la usa para actualizar el historial sin releer de Pinot, que aún
    // no la ha ingerido.
  ): Observable<ApiEnvelope<{ prospecto: Prospecto; transicion: TransicionPipeline }>> {
    return this.http.post<ApiEnvelope<{ prospecto: Prospecto; transicion: TransicionPipeline }>>(
      `${this.base}/${idprospecto}/pipeline`,
      body,
    );
  }
}
