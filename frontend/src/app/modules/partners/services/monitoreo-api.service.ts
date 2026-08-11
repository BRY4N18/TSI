import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import type { ApiEnvelope } from './partner-api.service';
import type { ConsumoPartner, LogLlamada, ReporteMensual } from './models/monitoreo.types';

export interface FiltrosLogs {
  idpartner: number;
  soloErrores?: boolean;
  /** Código HTTP exacto. Manda sobre `soloErrores` si se envían los dos. */
  codigohttp?: number | null;
  /** Rango temporal en epoch ms, resuelto en la base. */
  desdeMs?: number | null;
  hastaMs?: number | null;
  /**
   * Cursor **compuesto**: los dos campos por los que ordena el backend.
   * Con solo el id, la página siguiente repite o se salta filas cuando el id
   * no desciende con la fecha.
   */
  cursor?: number | null;
  cursorFecha?: number | null;
  limit?: number;
}

/**
 * Cliente REST del monitoreo de consumo (#08).
 *
 * Separado de `PartnerApiService` a propósito: son dos contratos distintos
 * (incorporación vs. consumo) y mezclarlos haría crecer un archivo ya cargado.
 *
 * **Paginación real por cursor** (`BE-DELTA-06`). El `next_cursor` del `meta`
 * se le puede devolver al endpoint en el parámetro `cursor`: hasta 2026-08-10
 * lo anunciaba sin aceptarlo, que es peor que no ofrecerlo.
 */
@Injectable({ providedIn: 'root' })
export class MonitoreoApiService {
  private readonly http = inject(HttpClient);

  /** Métricas del período vigente del partner (RF-APM-007). */
  metricas(idpartner: number, entorno = 'Producción'): Observable<ApiEnvelope<ConsumoPartner>> {
    const params = new HttpParams().set('entorno', entorno);
    return this.http.get<ApiEnvelope<ConsumoPartner>>(
      `/api/v1/partners/${idpartner}/metricas`,
      { params },
    );
  }

  /**
   * Registros de llamadas de un partner (RF-APM-008).
   *
   * `idpartner` es **obligatorio**: sin él el backend responde 400. No existe
   * una vista de «todos los partners a la vez», aunque el docstring del backend
   * lo sugiera — manda el código, que es lo que se ejecuta.
   */
  logs(filtros: FiltrosLogs): Observable<ApiEnvelope<LogLlamada[]>> {
    let params = new HttpParams()
      .set('idpartner', String(filtros.idpartner))
      .set('limit', String(filtros.limit ?? 50));
    if (filtros.soloErrores) {
      params = params.set('solo_errores', 'true');
    }
    // Todos los filtros viajan al servidor: la consola no guarda una ventana
    // en memoria para filtrarla después. Cada cambio es una consulta, igual
    // que en el resto del sistema.
    if (filtros.codigohttp !== undefined && filtros.codigohttp !== null) {
      params = params.set('codigohttp', String(filtros.codigohttp));
    }
    if (filtros.desdeMs !== undefined && filtros.desdeMs !== null) {
      params = params.set('desde', String(filtros.desdeMs));
    }
    if (filtros.hastaMs !== undefined && filtros.hastaMs !== null) {
      params = params.set('hasta', String(filtros.hastaMs));
    }
    if (filtros.cursor !== undefined && filtros.cursor !== null) {
      params = params.set('cursor', String(filtros.cursor));
    }
    if (filtros.cursorFecha !== undefined && filtros.cursorFecha !== null) {
      params = params.set('cursor_fecha', String(filtros.cursorFecha));
    }
    return this.http.get<ApiEnvelope<LogLlamada[]>>('/api/v1/logs-api', { params });
  }

  /** Reporte de un mes cerrado (RF-APM-009). Un mes sin consumo devuelve ceros. */
  reporteMensual(
    idpartner: number,
    anio: number,
    mes: number,
  ): Observable<ApiEnvelope<ReporteMensual>> {
    const params = new HttpParams()
      .set('idpartner', String(idpartner))
      .set('anio', String(anio))
      .set('mes', String(mes));
    return this.http.get<ApiEnvelope<ReporteMensual>>('/api/v1/reportes-consumo', { params });
  }
}
