/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { DestroyRef } from '@angular/core';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';

import { SeguimientoSseService } from './seguimiento-sse.service';

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
});
