import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, from, map, switchMap } from 'rxjs';

import { EvidenciaOfflineStoreService } from './evidencia-offline-store.service';
import {
  ApiEnvelope,
  EvidenciaFotoData,
  EvidenciaFotoItem,
  EvidenciaFotoPendienteItem,
  EvidenciaItem,
  EvidenciaListData,
  EvidenciaNotaData,
  EvidenciaNotaItem,
  EvidenciaNotaPendienteItem,
  RegistrarNotaCampoRequest,
  SincronizarEvidenciaData,
  SincronizarFotoMetadata,
  SincronizarNotaPendiente,
  TipoNotaCampo,
} from './models/evidencia-unidad.types';

@Injectable({ providedIn: 'root' })
export class EvidenciaApiService {
  private readonly http = inject(HttpClient);
  private readonly offlineStore = inject(EvidenciaOfflineStoreService);

  private evidenciasBase(idaccidente: string): string {
    return `/api/v1/accidentes/${idaccidente}/evidencias`;
  }

  listarServidor(
    idaccidente: string,
    params?: { tipo?: TipoNotaCampo; cursor?: string; limit?: number },
  ): Observable<ApiEnvelope<EvidenciaListData>> {
    let httpParams = new HttpParams();
    if (params?.tipo) {
      httpParams = httpParams.set('tipo', params.tipo);
    }
    if (params?.cursor) {
      httpParams = httpParams.set('cursor', params.cursor);
    }
    if (params?.limit != null) {
      httpParams = httpParams.set('limit', String(params.limit));
    }
    return this.http.get<ApiEnvelope<EvidenciaListData>>(this.evidenciasBase(idaccidente), {
      params: httpParams,
    });
  }

  listarConPendientesLocales(
    idaccidente: string,
    params?: { tipo?: TipoNotaCampo; cursor?: string; limit?: number },
  ): Observable<EvidenciaItem[]> {
    return this.listarServidor(idaccidente, params).pipe(
      switchMap((response) =>
        from(this.offlineStore.listarPendientes(idaccidente)).pipe(
          map(({ fotos, notas }) => {
            const servidor = response.data.items;
            const fotosLocales: EvidenciaFotoPendienteItem[] = fotos.map((foto) => ({
              tipo: 'foto' as const,
              local_id: foto.local_id,
              idaccidente: foto.idaccidente,
              urlevidenciafoto: foto.object_url,
              sincronizado: false as const,
              fechahora: foto.fechahora,
            }));
            const notasLocales: EvidenciaNotaPendienteItem[] = notas.map((nota) => ({
              tipo_evidencia: 'nota' as const,
              local_id: nota.local_id,
              idaccidente: nota.idaccidente,
              nota: nota.nota,
              tipo: nota.tipo,
              sincronizado: false as const,
              fechahora: nota.fechahora,
            }));
            return [...servidor, ...fotosLocales, ...notasLocales].sort(
              (a, b) => b.fechahora - a.fechahora,
            );
          }),
        ),
      ),
    );
  }

  subirFoto(
    idaccidente: string,
    archivo: File,
    fechahora?: number,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<EvidenciaFotoData>> {
    const form = new FormData();
    form.append('archivo', archivo);
    if (fechahora != null) {
      form.append('fechahora', String(fechahora));
    }
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.post<ApiEnvelope<EvidenciaFotoData>>(
      `${this.evidenciasBase(idaccidente)}/fotos`,
      form,
      { headers },
    );
  }

  registrarNota(
    idaccidente: string,
    body: RegistrarNotaCampoRequest,
    idempotencyKey?: string,
  ): Observable<ApiEnvelope<EvidenciaNotaData>> {
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined;
    return this.http.post<ApiEnvelope<EvidenciaNotaData>>(
      `${this.evidenciasBase(idaccidente)}/notas`,
      body,
      { headers },
    );
  }

  sincronizarPendientes(idaccidente: string): Observable<ApiEnvelope<SincronizarEvidenciaData>> {
    return from(this.offlineStore.listarPendientes(idaccidente)).pipe(
      switchMap(({ fotos, notas }) => {
        const form = new FormData();
        const notasPayload: SincronizarNotaPendiente[] = notas.map((nota) => ({
          local_id: nota.local_id,
          nota: nota.nota,
          tipo: nota.tipo,
          fechahora: nota.fechahora,
        }));
        const fotosMeta: SincronizarFotoMetadata[] = fotos.map((foto) => ({
          local_id: foto.local_id,
          fechahora: foto.fechahora,
        }));

        if (notasPayload.length) {
          form.append('notas', JSON.stringify(notasPayload));
        }
        if (fotosMeta.length) {
          form.append('fotos_metadata', JSON.stringify(fotosMeta));
          fotos.forEach((foto) => {
            form.append(
              'fotos',
              new File([foto.blob], `${foto.local_id}.jpg`, { type: foto.content_type }),
            );
          });
        }

        return this.http
          .post<ApiEnvelope<SincronizarEvidenciaData>>(
            `${this.evidenciasBase(idaccidente)}/sincronizar`,
            form,
          )
          .pipe(
            switchMap((response) =>
              from(this.limpiarSincronizados(response.data.resultados)).pipe(map(() => response)),
            ),
          );
      }),
    );
  }

  private async limpiarSincronizados(
    resultados: SincronizarEvidenciaData['resultados'],
  ): Promise<void> {
    await Promise.all(
      resultados
        .filter((item) => item.sincronizado)
        .map(async (item) => {
          if (item.idevidenciafoto != null) {
            await this.offlineStore.eliminarFoto(item.local_id);
          } else if (item.idnotaaccidentes != null) {
            await this.offlineStore.eliminarNota(item.local_id);
          }
        }),
    );
  }

  isFotoItem(item: EvidenciaItem): item is EvidenciaFotoItem | EvidenciaFotoPendienteItem {
    return 'tipo' in item && item.tipo === 'foto';
  }

  isNotaItem(item: EvidenciaItem): item is EvidenciaNotaItem | EvidenciaNotaPendienteItem {
    return 'tipo_evidencia' in item && item.tipo_evidencia === 'nota';
  }
}
