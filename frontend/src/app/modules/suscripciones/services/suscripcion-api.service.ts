import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  AltaSuscripcionRequest,
  CancelarSuscripcionRequest,
  RechazarCambioPlanRequest,
  RegularizacionEnvelope,
  SolicitudCambioPlanRequest,
  SolicitudEnvelope,
  SolicitudListEnvelope,
  SuscripcionDetalleEnvelope,
  SuscripcionEnvelope,
} from './models/suscripciones.types';

@Injectable({ providedIn: 'root' })
export class SuscripcionApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/suscripciones';

  alta(body: AltaSuscripcionRequest, idempotencyKey: string): Observable<SuscripcionEnvelope> {
    const headers = new HttpHeaders({ 'Idempotency-Key': idempotencyKey });
    return this.http.post<SuscripcionEnvelope>(this.base, body, { headers });
  }

  obtenerMiSuscripcion(): Observable<SuscripcionDetalleEnvelope> {
    return this.http.get<SuscripcionDetalleEnvelope>(`${this.base}/mia`);
  }

  cancelar(body: CancelarSuscripcionRequest, idempotencyKey: string): Observable<SuscripcionEnvelope> {
    const headers = new HttpHeaders({ 'Idempotency-Key': idempotencyKey });
    return this.http.post<SuscripcionEnvelope>(`${this.base}/mia/cancelar`, body, { headers });
  }

  reintentarCobro(idempotencyKey: string): Observable<RegularizacionEnvelope> {
    const headers = new HttpHeaders({ 'Idempotency-Key': idempotencyKey });
    return this.http.post<RegularizacionEnvelope>(`${this.base}/mia/reintentar-cobro`, null, {
      headers,
    });
  }

  listarSolicitudesCambioPlan(params?: {
    estado?: string;
    idcliente?: number;
    cursor?: string;
    limit?: number;
  }): Observable<SolicitudListEnvelope> {
    return this.http.get<SolicitudListEnvelope>(`${this.base}/solicitudes-cambio-plan`, {
      params: params as never,
    });
  }

  solicitarCambioPlan(
    body: SolicitudCambioPlanRequest,
    idempotencyKey: string,
  ): Observable<SolicitudEnvelope> {
    const headers = new HttpHeaders({ 'Idempotency-Key': idempotencyKey });
    return this.http.post<SolicitudEnvelope>(`${this.base}/solicitudes-cambio-plan`, body, {
      headers,
    });
  }

  aprobarCambioPlan(idsolicitud: number, idempotencyKey: string): Observable<SolicitudEnvelope> {
    const headers = new HttpHeaders({ 'Idempotency-Key': idempotencyKey });
    return this.http.post<SolicitudEnvelope>(
      `${this.base}/solicitudes-cambio-plan/${idsolicitud}/aprobar`,
      null,
      { headers },
    );
  }

  rechazarCambioPlan(
    idsolicitud: number,
    body: RechazarCambioPlanRequest,
    idempotencyKey: string,
  ): Observable<SolicitudEnvelope> {
    const headers = new HttpHeaders({ 'Idempotency-Key': idempotencyKey });
    return this.http.post<SolicitudEnvelope>(
      `${this.base}/solicitudes-cambio-plan/${idsolicitud}/rechazar`,
      body,
      { headers },
    );
  }
}
