/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { InformesOe2ApiService } from './informes-oe2-api.service';

describe('InformesOe2ApiService', () => {
  let api: InformesOe2ApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(InformesOe2ApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('obtener_incluye_slug_y_los_cuatro_params', () => {
    api
      .obtener('latencia-por-endpoint', {
        desde: '2026-08-01',
        hasta: '2026-08-16',
        granularidad: 'mes',
        comparacion: 'ninguna',
      })
      .subscribe();

    const req = http.expectOne(
      (r) => r.url === '/api/v1/informes-estrategicos/oe2/latencia-por-endpoint',
    );
    expect(req.request.url).not.toContain('informes-tacticos/partners');
    expect(req.request.params.get('desde')).toBe('2026-08-01');
    expect(req.request.params.get('hasta')).toBe('2026-08-16');
    expect(req.request.params.get('granularidad')).toBe('mes');
    expect(req.request.params.get('comparacion')).toBe('ninguna');
    expect(req.request.params.get('muestra_minima')).toBeNull();
    req.flush({ data: [], meta: {} });
  });

  it('no_expone_un_metodo_por_informe', () => {
    expect((api as unknown as { latenciaPorEndpoint?: unknown }).latenciaPorEndpoint).toBeUndefined();
  });

  it('no_llama_disponibilidad', () => {
    expect(JSON.stringify(api)).not.toContain('disponibilidad-api');
  });
});
