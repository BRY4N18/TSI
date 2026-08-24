/** @marker unit */
/**
 * PG-UI-005 — el canal en vivo no puede quedarse congelado fingiendo estar vivo.
 *
 * La única prueba que había aquí comprobaba que `streamDespacho()` devuelve algo
 * con `.subscribe` — es decir, que un `Observable` es un `Observable`. Pasaba
 * siempre y no cubría nada, mientras la página tenía dos defectos reales:
 *
 *   1. Ante un error marcaba `offline` y **no reintentaba nunca**: la vista de
 *      una emergencia en curso quedaba muerta hasta recargar, aunque la red
 *      volviera a los dos segundos.
 *   2. `complete` no estaba manejado, así que un cierre limpio del upstream
 *      dejaba el estado en `live` mostrando el último dato **como si fuera
 *      actual**. Nginx cierra streams largos sin error, así que ese es el caso
 *      habitual, no el raro.
 *
 * El segundo es el que persigue este plan: la pantalla no miente cuando falla,
 * miente cuando parece que funciona.
 */
import { provideHttpClient } from '@angular/common/http';
import { DestroyRef } from '@angular/core';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';

import { DespachoSseService } from './despacho-sse.service';

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

describe('DespachoSseService', () => {
  let service: DespachoSseService;
  let originalFetch: typeof fetch;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [DespachoSseService, provideHttpClient()] });
    service = TestBed.inject(DespachoSseService);
    originalFetch = window.fetch;
  });

  afterEach(() => {
    window.fetch = originalFetch;
  });

  it('streamResiliente_when_stream_falla_reintenta_tras_el_backoff', fakeAsync(() => {
    // Arrange
    const destroyRef = TestBed.inject(DestroyRef);
    let intentos = 0;
    window.fetch = jasmine.createSpy('fetch').and.callFake(() => {
      intentos++;
      return Promise.reject(new Error('network down'));
    });
    const estados: string[] = [];

    // Act
    const sub = service.streamResiliente('ACC-1', destroyRef).subscribe((u) => estados.push(u.estado));
    tick(0);

    // Assert — falló, avisó, y no reintenta de inmediato (eso sería un bucle)
    expect(estados).toEqual(['reconnecting', 'offline']);
    expect(intentos).toBe(1);

    // Act — pasa el backoff
    tick(5000);
    tick(0);

    // Assert — lo vuelve a intentar por su cuenta: nadie tiene que recargar
    expect(estados).toEqual(['reconnecting', 'offline', 'reconnecting', 'offline']);
    expect(intentos).toBe(2);

    sub.unsubscribe();
    tick(5000); // drena el retry pendiente para que fakeAsync no proteste
  }));

  // Reloj real, por el mismo motivo que el caso del cierre limpio: leer el
  // evento pasa por `await reader.read()`, y esas promesas son nativas del
  // navegador — `tick()` no las drena y el aserto se evaluaba con la lista aún
  // vacía. Se descubrió porque falló, no al escribirlo.
  it('streamResiliente_when_llega_un_evento_lo_entrega_marcado_como_live', async () => {
    // Arrange
    const destroyRef = TestBed.inject(DestroyRef);
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode('event: despacho\ndata: {"iddespacho": 7}\n\n'),
        );
        // se deja abierto a propósito
      },
    });
    window.fetch = jasmine.createSpy('fetch').and.resolveTo(new Response(stream, { status: 200 }));

    // Act
    const recibidos: unknown[] = [];
    const sub = service
      .streamResiliente('ACC-1', destroyRef)
      .subscribe((u) => u.evento && recibidos.push(u.evento));
    await waitFor(() => recibidos.length > 0);

    // Assert — el evento llega parseado, no como texto crudo
    expect(recibidos).toEqual([{ type: 'despacho', data: { iddespacho: 7 } }]);

    sub.unsubscribe();
  });

  /**
   * No puede correr bajo `fakeAsync`: el cierre se observa dentro de
   * `await reader.read()`, y las promesas internas de `ReadableStream` son
   * nativas —zone.js no las parchea— así que `tick()` no las drena nunca. Se
   * usa el reloj real con el backoff acortado por reflexión.
   */
  it('streamResiliente_when_el_upstream_cierra_limpio_degrada_a_offline', async () => {
    // Arrange
    const destroyRef = TestBed.inject(DestroyRef);
    (service as unknown as { RECONEXION_MS: number }).RECONEXION_MS = 20;

    let intentos = 0;
    window.fetch = jasmine.createSpy('fetch').and.callFake(() => {
      intentos++;
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          controller.enqueue(new TextEncoder().encode('event: ping\ndata: {}\n\n'));
          controller.close(); // cierre limpio, SIN error — lo que hace nginx
        },
      });
      return Promise.resolve(new Response(stream, { status: 200 }));
    });

    // Act
    const estados: string[] = [];
    const sub = service.streamResiliente('ACC-1', destroyRef).subscribe((u) => estados.push(u.estado));

    // Assert — **el aserto que importa**: un cierre sin error no puede dejar el
    // estado en `live`, porque la pantalla estaría diciendo «En vivo» sobre
    // datos que ya no se actualizan.
    await waitFor(() => estados.includes('offline'));
    expect(estados[estados.length - 1]).not.toBe('live');

    // Assert — y se reconecta sola
    await waitFor(() => intentos === 2);
    expect(intentos).toBe(2);

    sub.unsubscribe();
  });

  it('streamResiliente_when_el_consumidor_muere_deja_de_reintentar', fakeAsync(() => {
    // Un reintento que sobrevive a la pantalla es una fuga: seguiría pidiendo
    // el stream de un accidente que ya nadie mira, para siempre.
    const destroyRef = TestBed.inject(DestroyRef);
    let intentos = 0;
    window.fetch = jasmine.createSpy('fetch').and.callFake(() => {
      intentos++;
      return Promise.reject(new Error('network down'));
    });

    const sub = service.streamResiliente('ACC-1', destroyRef).subscribe();
    tick(0);
    expect(intentos).toBe(1);

    sub.unsubscribe();
    tick(30000);

    expect(intentos).toBe(1);
  }));
});
