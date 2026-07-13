/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { DisponibilidadUnidadApiService } from './disponibilidad-unidad-api.service';

describe('DisponibilidadUnidadApiService', () => {
  let service: DisponibilidadUnidadApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [DisponibilidadUnidadApiService],
    });
    service = TestBed.inject(DisponibilidadUnidadApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('consultarMiDisponibilidad_when_ok_returns_envelope', () => {
    // Arrange
    const mock = {
      data: {
        idunidademergencia: 1,
        estado_actual: 'Activa' as const,
        incluido_en_despacho: true,
        fechahora_ultimo_cambio: 1,
      },
      meta: { pagination: null },
    };

    // Act
    service.consultarMiDisponibilidad().subscribe((res) => {
      // Assert
      expect(res.data.estado_actual).toBe('Activa');
    });

    const req = http.expectOne('/api/v1/mi-unidad-emergencia/disponibilidad');
    expect(req.request.method).toBe('GET');
    req.flush(mock);
  });
});
