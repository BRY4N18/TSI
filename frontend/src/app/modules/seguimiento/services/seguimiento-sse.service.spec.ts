/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { DestroyRef } from '@angular/core';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';

import { SeguimientoSseService } from './seguimiento-sse.service';

/** Sondea `cond` con el reloj real hasta que se cumpla o se agote el plazo. */
async function waitFor(cond: () => boolean, timeoutMs = 2000): Promise<void> {
  const limite = Date.now() + timeoutMs;
  while (!cond()) {
    if (Date.now() > limite) {
      throw new Error('waitFor: condición no cumplida antes del timeout');
    }
    await new Promise((resolve) => setTimeout(resolve, 5));
  }
}

describe('SeguimientoSseService', () => {
  let service: SeguimientoSseService;
  let originalFetch: typeof fetch;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [SeguimientoSseService, provideHttpClient()] });
    service = TestBed.inject(SeguimientoSseService);
    originalFetch = window.fetch;
  });

  afterEach(() => {
    window.fetch = originalFetch;
  });

  it('connect_when_event_received_emits_parsed_payload', (done) => {
    // Arrange
    const payload = { idunidademergencia: 1, latitud: 19.43, longitud: -99.13 };
    const frame = `event: seguimiento.posicion\ndata: ${JSON.stringify(payload)}\n\n`;
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(frame));
        controller.close();
      },
    });
    window.fetch = jasmine
      .createSpy('fetch')
      .and.resolveTo(new Response(stream, { status: 200 }));

    // Act
    const sub = service.connect().subscribe((event) => {
      // Assert
      expect(event.type).toBe('seguimiento.posicion');
      expect(event.data).toEqual(payload);
      sub.unsubscribe();
      done();
    });
  });

  it('connectResiliente_when_stream_falla_reintenta_con_backoff_fijo', fakeAsync(() => {
    // Arrange
    const destroyRef = TestBed.inject(DestroyRef);
    let intentos = 0;
    window.fetch = jasmine.createSpy('fetch').and.callFake(() => {
      intentos++;
      return Promise.reject(new Error('network down'));
    });
    const estados: string[] = [];

    // Act
    const sub = service.connectResiliente(destroyRef).subscribe((update) => estados.push(update.estado));
    tick(0); // deja resolver el rechazo del primer intento

    // Assert — primer intento falló, sin reintento inmediato
    expect(estados).toEqual(['reconnecting', 'offline']);
    expect(intentos).toBe(1);

    // Act — pasa el backoff fijo (5s)
    tick(5000);
    tick(0);

    // Assert — reintentó una segunda vez
    expect(estados).toEqual(['reconnecting', 'offline', 'reconnecting', 'offline']);
    expect(intentos).toBe(2);

    sub.unsubscribe();
    tick(5000); // drena cualquier retry pendiente para que fakeAsync no falle
  }));

  it('connectResiliente_when_stream_abre_emite_live_sin_esperar_evento', fakeAsync(() => {
    const destroyRef = TestBed.inject(DestroyRef);
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(': connected\n\n'));
        // keep open — no close
      },
    });
    window.fetch = jasmine
      .createSpy('fetch')
      .and.resolveTo(new Response(stream, { status: 200 }));

    const estados: string[] = [];
    const sub = service.connectResiliente(destroyRef).subscribe((u) => estados.push(u.estado));
    tick(0);

    expect(estados).toContain('live');
    sub.unsubscribe();
  }));

  // Este caso no puede correr bajo `fakeAsync`: el cierre del stream se observa
  // dentro de `await reader.read()`, y las promesas internas de ReadableStream
  // son nativas del navegador (zone.js no las parchea), así que `tick()` nunca
  // las drena. Se usa el reloj real con el backoff acortado por reflexión.
  it('connectResiliente_when_stream_completa_reintenta', async () => {
    // Arrange
    const destroyRef = TestBed.inject(DestroyRef);
    const BACKOFF_MS = 20;
    (service as unknown as { RECONEXION_MS: number }).RECONEXION_MS = BACKOFF_MS;

    let intentos = 0;
    window.fetch = jasmine.createSpy('fetch').and.callFake(() => {
      intentos++;
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          controller.enqueue(new TextEncoder().encode(': connected\n\n'));
          controller.close();
        },
      });
      return Promise.resolve(new Response(stream, { status: 200 }));
    });

    const estados: string[] = [];
    const sub = service.connectResiliente(destroyRef).subscribe((u) => estados.push(u.estado));

    // Act — esperar a que el primer intento abra y luego se cierre solo
    await waitFor(() => estados.includes('offline'));

    // Assert — el cierre limpio del upstream degrada a offline, no queda colgado
    expect(estados).toContain('live');
    expect(intentos).toBe(1);

    // Act / Assert — y reprograma un reintento tras el backoff
    await waitFor(() => intentos === 2);
    expect(intentos).toBe(2);

    sub.unsubscribe();
  });
});
