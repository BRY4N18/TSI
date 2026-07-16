import { DestroyRef, Injectable, NgZone, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable, Subscription } from 'rxjs';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';
import { SeguimientoSseEvent, SeguimientoSseEventType } from '../models/seguimiento.types';

export type SeguimientoConexionEstado = 'live' | 'reconnecting' | 'offline';

export interface SeguimientoStreamUpdate {
  estado: SeguimientoConexionEstado;
  evento?: SeguimientoSseEvent;
}

/**
 * El `EventSource` nativo no puede mandar el header `Authorization`, y este
 * backend no usa autenticación por cookie (`withCredentials` no manda nada
 * útil aquí) — exige el mismo Bearer token que cualquier otro endpoint. Por
 * eso el stream se arma a mano con `fetch` (mismo patrón que
 * `DespachoSseService`), leyendo el body en streaming y parseando el formato
 * SSE (`event:`/`data:` separados por línea en blanco).
 */
@Injectable({ providedIn: 'root' })
export class SeguimientoSseService {
  private readonly zone = inject(NgZone);
  private readonly authApi = inject(AuthApiService);
  private readonly RECONEXION_MS = 5000;

  /**
   * Igual que `connect()`, pero se reconecta sola con backoff fijo mientras
   * el consumidor siga vivo (`destroyRef`). El stream termina ante cualquier
   * falla (red, backend, etc.) y sin reintento la pantalla se queda
   * mostrando datos congelados sin avisar — inaceptable en una vista de
   * monitoreo en vivo (RNF-SEG-001). Emite `{estado}` en cada transición de
   * conexión y `{estado: 'live', evento}` por cada evento recibido.
   */
  connectResiliente(destroyRef: DestroyRef): Observable<SeguimientoStreamUpdate> {
    return new Observable<SeguimientoStreamUpdate>((subscriber) => {
      let detenido = false;
      let retryHandle: ReturnType<typeof setTimeout> | undefined;
      let currentSub: Subscription | null = null;

      const intentar = () => {
        if (detenido) {
          return;
        }
        subscriber.next({ estado: 'reconnecting' });
        currentSub = this.connect().subscribe({
          next: (evento) => subscriber.next({ estado: 'live', evento }),
          error: () => {
            subscriber.next({ estado: 'offline' });
            if (!detenido) {
              retryHandle = setTimeout(intentar, this.RECONEXION_MS);
            }
          },
        });
      };

      intentar();

      return () => {
        detenido = true;
        currentSub?.unsubscribe();
        if (retryHandle !== undefined) {
          clearTimeout(retryHandle);
        }
      };
    }).pipe(takeUntilDestroyed(destroyRef));
  }

  connect(): Observable<SeguimientoSseEvent> {
    return new Observable((subscriber) => {
      const controller = new AbortController();
      const token = this.authApi.getAccessToken();

      fetch('/api/v1/seguimiento/stream', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: controller.signal,
      })
        .then(async (response) => {
          if (!response.ok || !response.body) {
            throw new Error(`SSE request failed with status ${response.status}`);
          }
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          for (;;) {
            const { value, done } = await reader.read();
            if (done) {
              break;
            }
            buffer += decoder.decode(value, { stream: true });
            const frames = buffer.split('\n\n');
            buffer = frames.pop() ?? '';
            for (const frame of frames) {
              const event = this.parseFrame(frame);
              if (event) {
                this.zone.run(() => subscriber.next(event));
              }
            }
          }
          this.zone.run(() => subscriber.complete());
        })
        .catch((err) => {
          if (controller.signal.aborted) {
            return;
          }
          this.zone.run(() => subscriber.error(err));
        });

      return () => controller.abort();
    });
  }

  private parseFrame(frame: string): SeguimientoSseEvent | null {
    let type: SeguimientoSseEventType | null = null;
    const dataLines: string[] = [];
    for (const line of frame.split('\n')) {
      if (line.startsWith('event:')) {
        type = line.slice(6).trim() as SeguimientoSseEventType;
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trim());
      }
    }
    if (!type || !dataLines.length) {
      return null;
    }
    try {
      return { type, data: JSON.parse(dataLines.join('\n')) };
    } catch {
      return null;
    }
  }
}
