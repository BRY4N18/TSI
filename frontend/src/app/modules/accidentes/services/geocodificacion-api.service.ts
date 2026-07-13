import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiEnvelope, GeocodificacionInversaData } from './models/accidente.types';

@Injectable({ providedIn: 'root' })
export class GeocodificacionApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/accidentes/geocodificacion-inversa';

  sugerir(latitud: number, longitud: number): Observable<ApiEnvelope<GeocodificacionInversaData>> {
    const params = new HttpParams()
      .set('latitud', String(latitud))
      .set('longitud', String(longitud));
    return this.http.get<ApiEnvelope<GeocodificacionInversaData>>(this.base, { params });
  }
}
