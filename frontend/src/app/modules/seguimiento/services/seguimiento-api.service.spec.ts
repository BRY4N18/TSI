/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { SeguimientoApiService } from './seguimiento-api.service';

describe('SeguimientoApiService', () => {
  let service: SeguimientoApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [SeguimientoApiService],
    });
    service = TestBed.inject(SeguimientoApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('obtenerMapa_when_ok_returns_data', () => {
    // Arrange
    const mock = {
      data: { accidentes_activos: [], unidades: [] },
      meta: { timestamp: '2026-07-09T00:00:00Z' },
    };

    // Act
    service.obtenerMapa().subscribe((res) => {
      // Assert
      expect(res.data.unidades).toEqual([]);
    });

    const req = http.expectOne('/api/v1/seguimiento/mapa');
    expect(req.request.method).toBe('GET');
    req.flush(mock);
  });

  it('cerrarCaso_when_ok_posts_payload', () => {
    // Arrange
    const mock = {
      data: { idaccidente: 'ACC-1', estado_caso: 'CERRADO' },
      meta: { timestamp: '2026-07-09T00:00:00Z' },
    };

    // Act
    service.cerrarCaso('ACC-1', { resultado_atencion: 'OK' }).subscribe((res) => {
      // Assert
      expect(res.data.estado_caso).toBe('CERRADO');
    });

    const req = http.expectOne('/api/v1/accidentes/ACC-1/cerrar');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ resultado_atencion: 'OK' });
    req.flush(mock);
  });
});
