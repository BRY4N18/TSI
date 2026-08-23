import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { EnvelopeInforme, PeriodoVista } from '../models/informes-oe1.types';

@Injectable({ providedIn: 'root' })
export class InformesOe1ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/informes-estrategicos/oe1';

  obtener(informe: string, periodo: PeriodoVista): Observable<EnvelopeInforme> {
    return this.http.get<EnvelopeInforme>(`${this.base}/${informe}`, {
      params: {
        desde: periodo.desde,
        hasta: periodo.hasta,
        granularidad: periodo.granularidad,
        comparacion: periodo.comparacion,
      },
    });
  }
}
