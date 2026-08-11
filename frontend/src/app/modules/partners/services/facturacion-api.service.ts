import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import type { ApiEnvelope } from './partner-api.service';
import type { ExcepcionFacturacion } from './models/monitoreo.types';

export interface MetaExcepciones {
  reintentos_agotados: number;
  no_tarificables: number;
}

/**
 * Excepciones de facturación de excedente (BE-DELTA-04/05).
 *
 * El endpoint lo abrió esta misma capa: la cola del Administrador no tenía de
 * dónde leer, y los partners no tarificables **no se persistían en ninguna
 * parte** — el único rastro era un correo.
 *
 * **No hay método de emisión.** No existe endpoint que emita una factura a
 * mano; exponer aquí un `emitir()` sería prometer algo que no se puede cumplir.
 */
@Injectable({ providedIn: 'root' })
export class FacturacionApiService {
  private readonly http = inject(HttpClient);

  excepciones(
    anio: number,
    mes: number,
  ): Observable<{ data: ExcepcionFacturacion[]; meta: MetaExcepciones }> {
    const params = new HttpParams().set('anio', String(anio)).set('mes', String(mes));
    return this.http.get<{ data: ExcepcionFacturacion[]; meta: MetaExcepciones }>(
      '/api/v1/facturacion/excepciones',
      { params },
    ) as Observable<{ data: ExcepcionFacturacion[]; meta: MetaExcepciones }>;
  }
}

/** Tipos del sobre estándar, reexportados por comodidad de los consumidores. */
export type { ApiEnvelope };
