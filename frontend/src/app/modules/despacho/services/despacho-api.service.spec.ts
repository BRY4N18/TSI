/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { DespachoApiService } from './despacho-api.service';

describe('DespachoApiService', () => {
  let service: DespachoApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [DespachoApiService],
    });
    service = TestBed.inject(DespachoApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('obtenerEstado_when_ok_returns_envelope', () => {
    const mock = {
      data: {
        idaccidente: 'ACC-1',
        estado_caso: 'BUSCANDO_UNIDAD' as const,
        tiempo_transcurrido_seg: 10,
        intentos: [],
        unidades_activas: [],
      },
      meta: {},
    };
    service.obtenerEstado('ACC-1').subscribe((res) => {
      expect(res.data.estado_caso).toBe('BUSCANDO_UNIDAD');
    });
    const req = http.expectOne('/api/v1/accidentes/ACC-1/despacho');
    expect(req.request.method).toBe('GET');
    req.flush(mock);
  });
});
