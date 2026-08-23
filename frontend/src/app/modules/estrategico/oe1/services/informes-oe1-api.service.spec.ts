/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { InformesOe1ApiService } from './informes-oe1-api.service';

describe('InformesOe1ApiService', () => {
  let api: InformesOe1ApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(InformesOe1ApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('obtener_usa_prefijo_oe1_y_cuatro_params', () => {
    api
      .obtener('mrr-mensual', {
        desde: '2026-08-01',
        hasta: '2026-08-16',
        granularidad: 'mes',
        comparacion: 'ninguna',
      })
      .subscribe();

    const req = http.expectOne((r) => r.url === '/api/v1/informes-estrategicos/oe1/mrr-mensual');
    expect(req.request.url).not.toContain('informes-tacticos');
    expect(req.request.url).not.toContain('/oe2/');
    expect(req.request.params.get('desde')).toBe('2026-08-01');
    expect(req.request.params.get('hasta')).toBe('2026-08-16');
    expect(req.request.params.get('granularidad')).toBe('mes');
    expect(req.request.params.get('comparacion')).toBe('ninguna');
    expect(req.request.params.get('umbral_muestra')).toBeNull();
    req.flush({ data: [], meta: {} });
  });

  it('un_solo_metodo_obtener', () => {
    expect((api as unknown as { mrrMensual?: unknown }).mrrMensual).toBeUndefined();
  });

  it('no_llama_slugs_bloqueados', () => {
    const serial = JSON.stringify(api);
    expect(serial).not.toContain('cac-por-canal');
    expect(serial).not.toContain('mercados-activos');
    expect(serial).not.toContain('cartera-mrr-por-mercado');
  });
});
