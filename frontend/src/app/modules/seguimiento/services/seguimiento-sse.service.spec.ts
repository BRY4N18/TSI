/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

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
});
