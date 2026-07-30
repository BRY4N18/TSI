import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, from, map, of } from 'rxjs';

import { EvidenciaOfflineStoreService } from './evidencia-offline-store.service';
import {
  ApiEnvelope,
  CatalogoListData,
  ClimaAccidenteData,
  ConductorAccidenteItem,
  ElementoFisicoAccidenteItem,
  EnriquecimientoAccidenteData,
  ImplicadoItem,
  RegistrarConductorAccidenteRequest,
  RegistrarImplicadoRequest,
  UpsertClimaAccidenteRequest,
} from './models/evidencia-unidad.types';

@Injectable({ providedIn: 'root' })
export class EnriquecimientoApiService {
  private readonly http = inject(HttpClient);
  private readonly offlineStore = inject(EvidenciaOfflineStoreService);

  private base(idaccidente: string): string {
    return `/api/v1/accidentes/${idaccidente}/enriquecimiento`;
  }

  consultar(idaccidente: string): Observable<ApiEnvelope<EnriquecimientoAccidenteData>> {
    return this.http.get<ApiEnvelope<EnriquecimientoAccidenteData>>(this.base(idaccidente));
  }

  upsertClima(
    idaccidente: string,
    body: UpsertClimaAccidenteRequest,
  ): Observable<ApiEnvelope<ClimaAccidenteData>> {
    if (!navigator.onLine) {
      return from(
        this.offlineStore.guardarClimaPendiente(
          idaccidente,
          body.idperiododia ?? null,
          body.idestadoclima ?? null,
        ),
      ).pipe(
        map(
          (local) =>
            ({
              data: {
                idaccidente,
                idperiododia: local.idperiododia,
                idestadoclima: local.idestadoclima,
                activo: true,
              },
              meta: { pagination: null },
            }) as ApiEnvelope<ClimaAccidenteData>,
        ),
      );
    }
    return this.http.put<ApiEnvelope<ClimaAccidenteData>>(`${this.base(idaccidente)}/clima`, body);
  }

  listarElementosFisicos(
    idaccidente: string,
  ): Observable<ApiEnvelope<{ items: ElementoFisicoAccidenteItem[] }>> {
    return this.http.get<ApiEnvelope<{ items: ElementoFisicoAccidenteItem[] }>>(
      `${this.base(idaccidente)}/elementos-fisicos`,
    );
  }

  agregarElementoFisico(
    idaccidente: string,
    body: { idelementofisico: number },
  ): Observable<ApiEnvelope<ElementoFisicoAccidenteItem>> {
    if (!navigator.onLine) {
      return from(
        this.offlineStore.guardarFisicoPendiente(idaccidente, body.idelementofisico),
      ).pipe(
        map(
          (local) =>
            ({
              data: {
                idelementosfisicosaccidente: 0,
                idaccidente,
                idelementofisico: local.idelementofisico,
                activo: true,
              },
              meta: { pagination: null },
            }) as ApiEnvelope<ElementoFisicoAccidenteItem>,
        ),
      );
    }
    return this.http.post<ApiEnvelope<ElementoFisicoAccidenteItem>>(
      `${this.base(idaccidente)}/elementos-fisicos`,
      body,
    );
  }

  desactivarElementoFisico(
    idaccidente: string,
    idelementosfisicosaccidente: number,
  ): Observable<ApiEnvelope<ElementoFisicoAccidenteItem>> {
    return this.http.patch<ApiEnvelope<ElementoFisicoAccidenteItem>>(
      `${this.base(idaccidente)}/elementos-fisicos/${idelementosfisicosaccidente}`,
      { activo: false },
    );
  }

  listarConductores(
    idaccidente: string,
  ): Observable<ApiEnvelope<{ items: ConductorAccidenteItem[] }>> {
    return this.http.get<ApiEnvelope<{ items: ConductorAccidenteItem[] }>>(
      `${this.base(idaccidente)}/conductores`,
    );
  }

  registrarConductor(
    idaccidente: string,
    body: RegistrarConductorAccidenteRequest,
  ): Observable<ApiEnvelope<ConductorAccidenteItem>> {
    if (!navigator.onLine) {
      return from(
        this.offlineStore.guardarConductorPendiente(
          idaccidente,
          body.conductor,
          body.idestadoconductor,
          body.vehiculo,
        ),
      ).pipe(
        map(
          () =>
            ({
              data: {
                idconductoraccidente: 0,
                idaccidente,
                idconductor: 0,
                idestadoconductor: body.idestadoconductor,
                idvehiculo: 0,
                activo: true,
                conductor: body.conductor,
                vehiculo: body.vehiculo,
              },
              meta: { pagination: null },
            }) as ApiEnvelope<ConductorAccidenteItem>,
        ),
      );
    }
    return this.http.post<ApiEnvelope<ConductorAccidenteItem>>(
      `${this.base(idaccidente)}/conductores`,
      body,
    );
  }

  desactivarConductor(
    idaccidente: string,
    idconductoraccidente: number,
  ): Observable<ApiEnvelope<ConductorAccidenteItem>> {
    return this.http.patch<ApiEnvelope<ConductorAccidenteItem>>(
      `${this.base(idaccidente)}/conductores/${idconductoraccidente}`,
      { activo: false },
    );
  }

  listarImplicados(
    idaccidente: string,
  ): Observable<ApiEnvelope<{ items: ImplicadoItem[] }>> {
    return this.http.get<ApiEnvelope<{ items: ImplicadoItem[] }>>(
      `${this.base(idaccidente)}/implicados`,
    );
  }

  registrarImplicado(
    idaccidente: string,
    body: RegistrarImplicadoRequest,
  ): Observable<ApiEnvelope<ImplicadoItem>> {
    if (!navigator.onLine) {
      return from(this.offlineStore.guardarImplicadoPendiente(idaccidente, body)).pipe(
        map(
          () =>
            ({
              data: {
                idimplicado: 0,
                idaccidente,
                tipoimplicado: body.tipoimplicado,
                estadoimplicado: body.estadoimplicado,
                genero: body.genero ?? null,
                edad: body.edad ?? null,
                activo: true,
              },
              meta: { pagination: null },
            }) as ApiEnvelope<ImplicadoItem>,
        ),
      );
    }
    return this.http.post<ApiEnvelope<ImplicadoItem>>(
      `${this.base(idaccidente)}/implicados`,
      body,
    );
  }

  desactivarImplicado(
    idaccidente: string,
    idimplicado: number,
  ): Observable<ApiEnvelope<ImplicadoItem>> {
    return this.http.patch<ApiEnvelope<ImplicadoItem>>(
      `${this.base(idaccidente)}/implicados/${idimplicado}`,
      { activo: false },
    );
  }

  catalogoPeriodos(): Observable<ApiEnvelope<CatalogoListData>> {
    return this.http.get<ApiEnvelope<CatalogoListData>>('/api/v1/catalogos/periodos-dias');
  }

  catalogoClimas(): Observable<ApiEnvelope<CatalogoListData>> {
    return this.http.get<ApiEnvelope<CatalogoListData>>('/api/v1/catalogos/estados-climas');
  }

  catalogoElementosFisicos(): Observable<ApiEnvelope<CatalogoListData>> {
    return this.http.get<ApiEnvelope<CatalogoListData>>('/api/v1/catalogos/elementos-fisicos');
  }

  catalogoEstadosConductor(): Observable<ApiEnvelope<CatalogoListData>> {
    return this.http.get<ApiEnvelope<CatalogoListData>>('/api/v1/catalogos/estados-conductor');
  }

  buildEnriquecimientoFormField(idaccidente: string): Observable<string | null> {
    return from(this.offlineStore.listarEnriquecimientoPendiente(idaccidente)).pipe(
      map((pendientes) => {
        if (
          !pendientes.clima &&
          !pendientes.elementos_fisicos.length &&
          !pendientes.conductores.length &&
          !pendientes.implicados.length
        ) {
          return null;
        }
        return JSON.stringify({
          clima: pendientes.clima
            ? {
                local_id: pendientes.clima.local_id,
                idperiododia: pendientes.clima.idperiododia,
                idestadoclima: pendientes.clima.idestadoclima,
              }
            : undefined,
          elementos_fisicos: pendientes.elementos_fisicos.map((f) => ({
            local_id: f.local_id,
            idelementofisico: f.idelementofisico,
          })),
          conductores: pendientes.conductores.map((c) => ({
            local_id: c.local_id,
            conductor: c.conductor,
            idestadoconductor: c.idestadoconductor,
            vehiculo: c.vehiculo,
          })),
          implicados: pendientes.implicados.map((i) => ({
            local_id: i.local_id,
            ...i.payload,
          })),
        });
      }),
    );
  }

  limpiarEnriquecimientoSincronizado(
    resultados: Array<{ local_id: string; sincronizado: boolean }>,
  ): Observable<void> {
    const ids = resultados.filter((r) => r.sincronizado).map((r) => r.local_id);
    if (!ids.length) {
      return of(undefined);
    }
    return from(
      Promise.all(
        ids.map(async (localId) => {
          await this.offlineStore.eliminarClima(localId);
          await this.offlineStore.eliminarFisico(localId);
          await this.offlineStore.eliminarConductor(localId);
          await this.offlineStore.eliminarImplicado(localId);
        }),
      ),
    ).pipe(map(() => undefined));
  }
}
