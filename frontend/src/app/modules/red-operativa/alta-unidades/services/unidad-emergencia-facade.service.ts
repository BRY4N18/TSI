import { Injectable, inject } from '@angular/core';
import { Observable, catchError, of } from 'rxjs';
import { map } from 'rxjs/operators';

import { UnidadEmergenciaApiService } from './unidad-emergencia-api.service';
import {
  ApiEnvelope,
  BajaUnidadData,
  DisponibilidadData,
  ImportacionLoteData,
  UnidadCreateRequest,
  UnidadCreatedData,
  UnidadEmergenciaData,
  UnidadPatchRequest,
  UnidadUpdatedData,
} from '../models/unidad-emergencia.contract';

export interface OperationResult<T> {
  ok: boolean;
  data?: T;
  error?: string;
}

@Injectable({ providedIn: 'root' })
export class UnidadEmergenciaFacadeService {
  private readonly api = inject(UnidadEmergenciaApiService);

  registrar(body: UnidadCreateRequest): Observable<OperationResult<UnidadCreatedData>> {
    if (body.tipopropiedad === 'Externa' && !body.contactoproveedor) {
      return of({ ok: false, error: 'contactoproveedor es requerido para unidades Externa' });
    }
    return this.wrap(this.api.registrar(body));
  }

  editar(
    idunidademergencia: number,
    body: UnidadPatchRequest,
    confirmarEdicionCritica = false,
  ): Observable<OperationResult<UnidadUpdatedData>> {
    return this.wrap(this.api.editar(idunidademergencia, body, confirmarEdicionCritica));
  }

  importarLote(archivo: File): Observable<OperationResult<ImportacionLoteData>> {
    return this.wrap(this.api.importarLote(archivo));
  }

  darDeBaja(
    idunidademergencia: number,
    motivo: string,
    forzar = false,
  ): Observable<OperationResult<BajaUnidadData>> {
    if (!motivo.trim()) {
      return of({ ok: false, error: 'El motivo es requerido' });
    }
    return this.wrap(this.api.darDeBaja(idunidademergencia, motivo, forzar));
  }

  reactivar(idunidademergencia: number): Observable<OperationResult<UnidadEmergenciaData>> {
    return this.wrap(this.api.reactivar(idunidademergencia));
  }

  declararDisponibilidad(
    idunidademergencia: number,
    estadonuevo: string,
  ): Observable<OperationResult<DisponibilidadData>> {
    if (estadonuevo === 'En Misión') {
      return of({ ok: false, error: '"En Misión" es de asignación exclusiva del sistema' });
    }
    return this.wrap(this.api.declararDisponibilidad(idunidademergencia, estadonuevo));
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
