import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiEnvelope, NotificacionVentas } from '../models/notificacion-ventas.types';

@Injectable({ providedIn: 'root' })
export class NotificacionApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/ventas-crm/notificaciones';

  listar(params?: {
    cursor?: string;
    limit?: number;
    idusuario?: number;
    regladisparada?: string;
    id_prospecto?: number;
  }): Observable<ApiEnvelope<NotificacionVentas[]>> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          httpParams = httpParams.set(k, String(v));
        }
      });
    }
    return this.http.get<ApiEnvelope<NotificacionVentas[]>>(this.base, { params: httpParams });
  }
}
