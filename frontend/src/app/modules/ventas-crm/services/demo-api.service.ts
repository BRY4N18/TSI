import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  AbrirSesionDemoRequest,
  ApiEnvelope,
  InteraccionDemo,
  InteraccionDemoRequest,
  SesionDemo,
} from '../models/notificacion-ventas.types';

@Injectable({ providedIn: 'root' })
export class DemoApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/ventas-crm/demo';

  abrirSesion(body: AbrirSesionDemoRequest): Observable<ApiEnvelope<SesionDemo>> {
    return this.http.post<ApiEnvelope<SesionDemo>>(`${this.base}/sesiones`, body);
  }

  registrarInteraccion(
    body: InteraccionDemoRequest,
  ): Observable<ApiEnvelope<InteraccionDemo>> {
    return this.http.post<ApiEnvelope<InteraccionDemo>>(`${this.base}/interacciones`, body);
  }
}
