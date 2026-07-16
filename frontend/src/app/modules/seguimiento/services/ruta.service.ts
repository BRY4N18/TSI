import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import * as L from 'leaflet';
import { Observable, catchError, map, of, timeout } from 'rxjs';

import { ApiEnvelope } from '../models/seguimiento.types';

interface RutaData {
  puntos: { latitud: number; longitud: number }[];
}

/**
 * Calcula la ruta por calles reales entre dos puntos (unidad → accidente) vía
 * el proxy de Django hacia OSRM. Si el motor de ruteo falla, no responde a
 * tiempo, o no encuentra ruta, degrada a la línea recta [origen, destino] —
 * esta vista es de monitoreo/visualización, nunca debe romperse ni bloquear
 * por un fallo de un servicio auxiliar de ruteo.
 */
@Injectable({ providedIn: 'root' })
export class RutaService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1';
  private readonly TIMEOUT_MS = 3000;

  calcularRuta(origen: L.LatLng, destino: L.LatLng): Observable<L.LatLngExpression[]> {
    const recta: L.LatLngExpression[] = [origen, destino];

    return this.http
      .get<ApiEnvelope<RutaData>>(`${this.baseUrl}/seguimiento/ruta`, {
        params: {
          origen: `${origen.lat},${origen.lng}`,
          destino: `${destino.lat},${destino.lng}`,
        },
      })
      .pipe(
        timeout(this.TIMEOUT_MS),
        map((res) =>
          res.data.puntos.length
            ? res.data.puntos.map((p): L.LatLngExpression => L.latLng(p.latitud, p.longitud))
            : recta,
        ),
        catchError(() => of(recta)),
      );
  }
}
