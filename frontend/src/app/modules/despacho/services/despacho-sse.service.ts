import { DestroyRef, Injectable, NgZone, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable, Subscription } from 'rxjs';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

export interface DespachoStreamEvent {
  type: string;
  data: unknown;
}

export type DespachoConexionEstado = 'live' | 'reconnecting' | 'offline';

export interface DespachoStreamUpdate {
  estado: DespachoConexionEstado;
  evento?: DespachoStreamEvent;
}

/**
 * El navegador `EventSource` nativo no permite mandar headers propios, así que
 * no puede llevar el `Authorization: Bearer <token>` que el backend exige
 * (JWTSessionAuthentication, igual que cualquier otro endpoint). Por eso este
 * servicio arma el stream a mano con `fetch` (que sí manda el header) y
 * parsea el formato SSE (`event:`/`data:` separados por línea en blanco) del
 * body en streaming.
 */
@Injectable({ providedIn: 'root' })
export class DespachoSseService {
  private readonly zone = inject(NgZone);
  private readonly authApi = inject(AuthApiService);
  private readonly RECONEXION_MS = 5000;

  /**
   * Igual que `streamDespacho()`, pero se reconecta sola mientras el consumidor
   * siga vivo.
   *
   * **El defecto que corrige (PG-UI-005).** La pagina de monitoreo se suscribia
   * a `streamDespacho()` directamente: ante un error marcaba `offline` y **no
   * volvia a intentarlo nunca**, asi que la vista de una emergencia en curso
   * quedaba muerta hasta que alguien recargase, aunque la red hubiera vuelto a
   * los dos segundos.
   *
   * Peor era el cierre limpio: `complete` no estaba manejado, asi que el estado
   * se quedaba en `live` mostrando el ultimo dato recibido **como si fuera
   * actual**. Nginx cierra streams largos sin error, de modo que ese no es el
   * caso raro sino el habitual — y es exactamente el fallo que la regla
   * persigue: la pantalla no miente al fallar, miente al parecer que funciona.
   */
  streamResiliente(idaccidente: string, destroyRef: DestroyRef): Observable<DespachoStreamUpdate> {
    return new Observable<DespachoStreamUpdate>((subscriber) => {
      let detenido = false;
      let retryHandle: ReturnType<typeof setTimeout> | undefined;
      let currentSub: Subscription | null = null;

      const programarReintento = () => {
        if (!detenido) {
          retryHandle = setTimeout(intentar, this.RECONEXION_MS);
        }
      };

      const intentar = () => {
        if (detenido) {
          return;
        }
        subscriber.next({ estado: 'reconnecting' });
        currentSub = this.streamDespacho(idaccidente).subscribe({
          next: (evento) => subscriber.next({ estado: 'live', evento }),
          error: () => {
            subscriber.next({ estado: 'offline' });
            programarReintento();
          },
          complete: () => {
            // Cierre limpio del upstream: tambien deja de haber datos frescos.
            subscriber.next({ estado: 'offline' });
            programarReintento();
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

  streamDespacho(idaccidente: string): Observable<DespachoStreamEvent> {
    return new Observable((subscriber) => {
      const controller = new AbortController();
      const token = this.authApi.getAccessToken();

      fetch(`/api/v1/accidentes/${idaccidente}/despacho/stream`, {
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

  private parseFrame(frame: string): DespachoStreamEvent | null {
    let type = 'message';
    const dataLines: string[] = [];
    for (const line of frame.split('\n')) {
      if (line.startsWith('event:')) {
        type = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trim());
      }
    }
    if (!dataLines.length) {
      return null;
    }
    const raw = dataLines.join('\n');
    let data: unknown = raw;
    try {
      data = JSON.parse(raw);
    } catch {
      /* no era JSON, se conserva el texto crudo */
    }
    return { type, data };
  }
}
