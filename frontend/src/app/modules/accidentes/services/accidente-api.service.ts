import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ActualizarAccidenteData,
  ActualizarAccidenteRequest,
  ApiEnvelope,
  ConfirmarReporteData,
  ConfirmarReporteRequest,
  DescartarCasoData,
  DescartarCasoRequest,
  EscalarSeveridadData,
  EscalarSeveridadRequest,
  EstadoAccidente,
  FusionarReportesData,
  FusionarReportesRequest,
  AccidenteDetalle,
  AccidenteListItem,
  RegistrarAccidenteData,
  RegistrarAccidenteRequest,
} from './models/accidente.types';

export interface AccidenteListFilters {
  idseveridad?: number;
  estado?: EstadoAccidente;
  activo?: boolean;
  fechaDesde?: number;
  fechaHasta?: number;
  idciudad?: number;
  idestadoregion?: number;
  limit?: number;
}

@Injectable({ providedIn: 'root' })
export class AccidenteApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/accidentes';

  listar(filters: AccidenteListFilters = {}): Observable<ApiEnvelope<AccidenteListItem[]>> {
    let params = new HttpParams().set('limit', String(filters.limit ?? 20));
    if (filters.idseveridad !== undefined) {
      params = params.set('idseveridad', String(filters.idseveridad));
    }
    if (filters.estado !== undefined) {
      params = params.set('estado', filters.estado);
    }
    if (filters.activo !== undefined) {
      params = params.set('activo', String(filters.activo));
    }
    if (filters.fechaDesde !== undefined) {
      params = params.set('fecha_desde', String(filters.fechaDesde));
    }
    if (filters.fechaHasta !== undefined) {
      params = params.set('fecha_hasta', String(filters.fechaHasta));
    }
    if (filters.idciudad !== undefined) {
      params = params.set('idciudad', String(filters.idciudad));
    }
    if (filters.idestadoregion !== undefined) {
      params = params.set('idestadoregion', String(filters.idestadoregion));
    }
    return this.http.get<ApiEnvelope<AccidenteListItem[]>>(this.base, { params });
  }

  detalle(idaccidente: string): Observable<ApiEnvelope<AccidenteDetalle>> {
    return this.http.get<ApiEnvelope<AccidenteDetalle>>(`${this.base}/${idaccidente}`);
  }

  actualizar(
    idaccidente: string,
    body: ActualizarAccidenteRequest,
  ): Observable<ApiEnvelope<ActualizarAccidenteData>> {
    return this.http.patch<ApiEnvelope<ActualizarAccidenteData>>(
      `${this.base}/${idaccidente}`,
      body,
    );
  }

  registrar(
    body: RegistrarAccidenteRequest,
    forzarAdvertencias = false,
  ): Observable<ApiEnvelope<RegistrarAccidenteData>> {
    const params = new HttpParams().set(
      'forzarAdvertencias',
      String(forzarAdvertencias),
    );
    return this.http.post<ApiEnvelope<RegistrarAccidenteData>>(this.base, body, { params });
  }

  confirmarReporte(
    idaccidente: string,
    body: ConfirmarReporteRequest,
  ): Observable<ApiEnvelope<ConfirmarReporteData>> {
    return this.http.post<ApiEnvelope<ConfirmarReporteData>>(
      `${this.base}/${idaccidente}/confirmar-reporte`,
      body,
    );
  }

  descartar(
    idaccidente: string,
    body: DescartarCasoRequest = {},
  ): Observable<ApiEnvelope<DescartarCasoData>> {
    return this.http.post<ApiEnvelope<DescartarCasoData>>(
      `${this.base}/${idaccidente}/descartar`,
      body,
    );
  }

  fusionar(
    idaccidenteDuplicado: string,
    body: FusionarReportesRequest,
  ): Observable<ApiEnvelope<FusionarReportesData>> {
    return this.http.post<ApiEnvelope<FusionarReportesData>>(
      `${this.base}/${idaccidenteDuplicado}/fusionar`,
      body,
    );
  }

  escalarSeveridad(
    idaccidente: string,
    body: EscalarSeveridadRequest,
  ): Observable<ApiEnvelope<EscalarSeveridadData>> {
    return this.http.post<ApiEnvelope<EscalarSeveridadData>>(
      `${this.base}/${idaccidente}/escalar-severidad`,
      body,
    );
  }
}
