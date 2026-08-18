import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { rutaHttpDe } from '../definiciones/pantallas-gestion.definiciones';
import { EnvelopeInforme, PeriodoVista } from '../models/informes-compuestos.types';

@Injectable({ providedIn: 'root' })
export class InformesCompuestosApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/informes-tacticos/soporte';

  obtener(
    informe: string,
    periodo: PeriodoVista,
    extra?: { agrupar_por?: string },
  ): Observable<EnvelopeInforme> {
    const params: Record<string, string> = {
      desde: periodo.desde,
      hasta: periodo.hasta,
    };
    if (extra?.agrupar_por) {
      params['agrupar_por'] = extra.agrupar_por;
    }
    return this.http.get<EnvelopeInforme>(`${this.base}/${rutaHttpDe(informe)}`, {
      params,
    });
  }
}
