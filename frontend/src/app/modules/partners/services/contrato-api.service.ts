import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import type { ApiEnvelope } from './partner-api.service';
import type { ContratoIntegracion } from './models/partner.types';

/**
 * Contrato de integración versionado (CU-O50, RF-PON-011).
 *
 * `id_servicio` es obligatorio a propósito: el versionado es POR SERVICIO, y
 * pedir «la versión vigente» sin decir de cuál sería una respuesta ambigua en
 * cuanto exista el segundo servicio.
 */
@Injectable({ providedIn: 'root' })
export class ContratoApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/contrato-integracion';

  consultar(idServicio: number, version?: string): Observable<ApiEnvelope<ContratoIntegracion>> {
    let params = new HttpParams().set('id_servicio', String(idServicio));
    if (version) {
      params = params.set('version', version);
    }
    return this.http.get<ApiEnvelope<ContratoIntegracion>>(this.base, { params });
  }
}
