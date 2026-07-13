/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { DespachoParametrosApiService } from './despacho-parametros-api.service';

describe('DespachoParametrosApiService', () => {
  let service: DespachoParametrosApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [DespachoParametrosApiService],
    });
    service = TestBed.inject(DespachoParametrosApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('obtener_when_ok_returns_params', () => {
    service.obtener().subscribe((res) => {
      expect(res.data.timeout_respuesta_seg).toBe(90);
    });
    const req = http.expectOne('/api/v1/despacho/parametros');
    req.flush({
      data: {
        timeout_respuesta_seg: 90,
        peso_distancia_pct: 60,
        peso_concordancia_pct: 25,
        peso_disponibilidad_pct: 15,
        prioridades_por_severidad: [],
      },
      meta: {},
    });
  });
});
