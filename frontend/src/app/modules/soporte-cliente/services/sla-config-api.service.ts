import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiEnvelope, CrearSLAConfigRequest, SLAConfig } from './models/soporte.types';

@Injectable({ providedIn: 'root' })
export class SlaConfigApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/soporte/sla-config';

  listar(): Observable<ApiEnvelope<{ items: SLAConfig[] }>> {
    return this.http.get<ApiEnvelope<{ items: SLAConfig[] }>>(this.base);
  }

  crear(body: CrearSLAConfigRequest): Observable<ApiEnvelope<SLAConfig>> {
    return this.http.post<ApiEnvelope<SLAConfig>>(this.base, body);
  }

  modificar(
    idslaconfig: number,
    tiemporespuestamax: number,
    tiemporesolucionmax: number,
  ): Observable<ApiEnvelope<SLAConfig>> {
    return this.http.patch<ApiEnvelope<SLAConfig>>(`${this.base}/${idslaconfig}`, {
      tiemporespuestamax,
      tiemporesolucionmax,
    });
  }
}
