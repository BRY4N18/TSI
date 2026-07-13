import { Injectable, NgZone, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

export interface DespachoStreamEvent {
  type: string;
  data: unknown;
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
