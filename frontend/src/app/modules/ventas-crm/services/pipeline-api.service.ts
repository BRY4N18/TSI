import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiEnvelope, PipelineTransicionRequest, Prospecto } from '../models/prospectos.types';

@Injectable({ providedIn: 'root' })
export class PipelineApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/ventas-crm/prospectos';

  registrarTransicion(
    idprospecto: number,
    body: PipelineTransicionRequest,
  ): Observable<ApiEnvelope<{ prospecto: Prospecto }>> {
    return this.http.post<ApiEnvelope<{ prospecto: Prospecto }>>(
      `${this.base}/${idprospecto}/pipeline`,
      body,
    );
  }
}
