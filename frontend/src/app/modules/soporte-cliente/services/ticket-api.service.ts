import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  DashboardSoporteData,
  RegistrarTicketRequest,
  Ticket,
  TicketDetalleData,
  TransicionTicketData,
} from './models/soporte.types';

@Injectable({ providedIn: 'root' })
export class TicketApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/soporte/tickets';

  listar(params?: {
    idestadosoporte?: string;
    prioridad?: string;
  }): Observable<ApiEnvelope<{ items: Ticket[] }>> {
    return this.http.get<ApiEnvelope<{ items: Ticket[] }>>(this.base, {
      params: { ...params },
    });
  }

  registrar(body: RegistrarTicketRequest): Observable<ApiEnvelope<Ticket>> {
    return this.http.post<ApiEnvelope<Ticket>>(this.base, body);
  }

  obtenerDetalle(idReclamo: number): Observable<ApiEnvelope<TicketDetalleData>> {
    return this.http.get<ApiEnvelope<TicketDetalleData>>(`${this.base}/${idReclamo}`);
  }

  clasificarManual(
    idReclamo: number,
    tipoIncidencia: string,
    prioridad: string,
  ): Observable<ApiEnvelope<Ticket>> {
    return this.http.post<ApiEnvelope<Ticket>>(`${this.base}/${idReclamo}/clasificar`, {
      tipo_incidencia: tipoIncidencia,
      prioridad,
    });
  }

  tomar(idReclamo: number): Observable<ApiEnvelope<TransicionTicketData>> {
    return this.http.post<ApiEnvelope<TransicionTicketData>>(
      `${this.base}/${idReclamo}/tomar`,
      {},
    );
  }

  comentar(
    idReclamo: number,
    mensaje: string,
    esNotaInterna: boolean,
  ): Observable<ApiEnvelope<unknown>> {
    return this.http.post<ApiEnvelope<unknown>>(`${this.base}/${idReclamo}/comentarios`, {
      mensaje,
      es_nota_interna: esNotaInterna,
    });
  }

  escalar(
    idReclamo: number,
    idRolEscalar: string,
    idAgenteAsignado: number,
    mensaje?: string,
  ): Observable<ApiEnvelope<TransicionTicketData>> {
    return this.http.post<ApiEnvelope<TransicionTicketData>>(`${this.base}/${idReclamo}/escalar`, {
      id_rol_escalar: idRolEscalar,
      id_agente_asignado: idAgenteAsignado,
      mensaje,
    });
  }

  resolver(idReclamo: number, mensaje?: string): Observable<ApiEnvelope<TransicionTicketData>> {
    return this.http.post<ApiEnvelope<TransicionTicketData>>(`${this.base}/${idReclamo}/resolver`, {
      mensaje,
    });
  }

  confirmarCierre(idReclamo: number): Observable<ApiEnvelope<TransicionTicketData>> {
    return this.http.post<ApiEnvelope<TransicionTicketData>>(
      `${this.base}/${idReclamo}/confirmar-cierre`,
      {},
    );
  }

  reabrir(idReclamo: number, motivo?: string): Observable<ApiEnvelope<TransicionTicketData>> {
    const formData = new FormData();
    if (motivo) {
      formData.append('motivo', motivo);
    }
    return this.http.post<ApiEnvelope<TransicionTicketData>>(
      `${this.base}/${idReclamo}/reabrir`,
      formData,
    );
  }

  dashboard(): Observable<ApiEnvelope<DashboardSoporteData>> {
    return this.http.get<ApiEnvelope<DashboardSoporteData>>('/api/v1/soporte/dashboard');
  }
}
