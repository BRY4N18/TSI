/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { MiSeguimientoApiService } from './mi-seguimiento-api.service';

describe('MiSeguimientoApiService', () => {
  let service: MiSeguimientoApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [MiSeguimientoApiService],
    });
    service = TestBed.inject(MiSeguimientoApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('registrarPosicion_when_ok_returns_aceptado', () => {
    // Arrange
    const payload = {
      idunidademergencia: 1,
      idaccidente: 'ACC-1',
      latitud: 19.43,
      longitud: -99.13,
      fechahora: 1_700_000_000_000,
    };
    const mock = {
      data: { aceptado: true, llegada_automatica: false },
      meta: { timestamp: '2026-07-09T00:00:00Z' },
    };

    // Act
    service.registrarPosicion(payload).subscribe((res) => {
      // Assert
      expect(res.data.aceptado).toBeTrue();
    });

    const req = http.expectOne('/api/v1/mi-seguimiento/posicion');
    expect(req.request.method).toBe('POST');
    req.flush(mock);
  });

  it('abortarMision_when_ok_posts_motivo', () => {
    // Arrange
    const mock = {
      data: { iddespacho: 1, estado_despacho: 'Abortado', reasignacion_disparada: true },
      meta: { timestamp: '2026-07-09T00:00:00Z' },
    };

    // Act
    service.abortarMision(1, { motivo: 'Bloqueo' }).subscribe();

    const req = http.expectOne('/api/v1/mi-seguimiento/despachos/1/abortar');
    expect(req.request.body).toEqual({ motivo: 'Bloqueo' });
    req.flush(mock);
  });
});
