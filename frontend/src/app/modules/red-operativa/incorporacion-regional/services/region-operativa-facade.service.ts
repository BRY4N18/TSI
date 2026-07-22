import { Injectable, inject } from '@angular/core';
import { Observable, catchError, of } from 'rxjs';
import { map } from 'rxjs/operators';

import { RegionOperativaApiService } from './region-operativa-api.service';
import {
  ApiEnvelope,
  RechazoDefinitivoData,
  RegionEstadoData,
  ValidacionHistorialItem,
  ValidacionRegionData,
  ValidacionRegionRequest,
} from '../models/region-operativa.contract';

export interface OperationResult<T> {
  ok: boolean;
  data?: T;
  error?: string;
}

@Injectable({ providedIn: 'root' })
export class RegionOperativaFacadeService {
  private readonly api = inject(RegionOperativaApiService);

  ejecutarValidacion(
    body: ValidacionRegionRequest,
  ): Observable<OperationResult<ValidacionRegionData>> {
    if (body.resultado === 'Rechazada' && !body.motivo?.trim()) {
      return of({ ok: false, error: "El motivo es requerido cuando resultado='Rechazada'" });
    }
    return this.wrap(this.api.ejecutarValidacion(body));
  }

  listarHistorialValidacion(
    idregionoperativa: number,
  ): Observable<OperationResult<ValidacionHistorialItem[]>> {
    return this.wrap(this.api.listarHistorialValidacion(idregionoperativa));
  }

  rechazarDefinitivamente(
    idregionoperativa: number,
  ): Observable<OperationResult<RechazoDefinitivoData>> {
    return this.wrap(this.api.rechazarDefinitivamente(idregionoperativa));
  }

  reevaluarRegion(
    idregionoperativa: number,
    estadoregion: 'En_Alerta' | 'Despublicada',
    motivo: string,
  ): Observable<OperationResult<RegionEstadoData>> {
    if (!motivo.trim()) {
      return of({ ok: false, error: 'El motivo es requerido' });
    }
    return this.wrap(this.api.reevaluarRegion(idregionoperativa, estadoregion, motivo));
  }

  despublicarAutomaticamente(
    idregionoperativa: number,
  ): Observable<OperationResult<RegionEstadoData>> {
    return this.wrap(this.api.despublicarAutomaticamente(idregionoperativa));
  }

  private wrap<T>(source: Observable<ApiEnvelope<T>>): Observable<OperationResult<T>> {
    return source.pipe(
      map((res) => ({ ok: true, data: res.data }) as OperationResult<T>),
      catchError((err) => of({ ok: false, error: this.extractError(err) })),
    );
  }

  private extractError(err: unknown): string {
    const detail = (err as { error?: { detail?: string } })?.error?.detail;
    return detail ?? 'Ocurrió un error al procesar la solicitud';
  }
}
