import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

import { ApiEnvelope, CatalogoItem } from './models/accidente.types';

/**
 * Catálogo geográfico en cascada (RF-REG-006 punto 3, Escenario 5).
 * Contrato: specs/003-operational/Emergencias/registro-accidente/contracts/registro-accidente.openapi.yaml
 */
@Injectable({ providedIn: 'root' })
export class UbicacionCatalogoApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/accidentes';

  listarPaises(): Observable<CatalogoItem[]> {
    return this.http
      .get<ApiEnvelope<CatalogoItem[]>>(`${this.base}/paises`)
      .pipe(map((res) => res.data));
  }

  listarEstados(idpais: number): Observable<CatalogoItem[]> {
    const params = new HttpParams().set('idpais', String(idpais));
    return this.http
      .get<ApiEnvelope<CatalogoItem[]>>(`${this.base}/estados`, { params })
      .pipe(map((res) => res.data));
  }

  listarCondados(idestado: number): Observable<CatalogoItem[]> {
    const params = new HttpParams().set('idestado', String(idestado));
    return this.http
      .get<ApiEnvelope<CatalogoItem[]>>(`${this.base}/condados`, { params })
      .pipe(map((res) => res.data));
  }

  listarCiudades(idcondado: number): Observable<CatalogoItem[]> {
    const params = new HttpParams().set('idcondado', String(idcondado));
    return this.http
      .get<ApiEnvelope<CatalogoItem[]>>(`${this.base}/ciudades`, { params })
      .pipe(map((res) => res.data));
  }

  listarCalles(idciudad: number): Observable<CatalogoItem[]> {
    const params = new HttpParams().set('idciudad', String(idciudad));
    return this.http
      .get<ApiEnvelope<CatalogoItem[]>>(`${this.base}/calles`, { params })
      .pipe(map((res) => res.data));
  }
}
