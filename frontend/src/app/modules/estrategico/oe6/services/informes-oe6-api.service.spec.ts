/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { InformesOe6ApiService } from './informes-oe6-api.service';

describe('InformesOe6ApiService', () => {
  let api: InformesOe6ApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(InformesOe6ApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('obtener_usa_prefijo_oe6_y_cuatro_params', () => {
    api
      .obtener('tiempo-respuesta-global', {
        desde: '2026-08-01',
        hasta: '2026-08-16',
        granularidad: 'mes',
        comparacion: 'ninguna',
      })
      .subscribe();

    const req = http.expectOne(
      (r) => r.url === '/api/v1/informes-estrategicos/oe6/tiempo-respuesta-global',
    );
    expect(req.request.url).not.toContain('informes-tacticos');
    expect(req.request.url).not.toContain('/oe3/');
    expect(req.request.params.get('desde')).toBe('2026-08-01');
    expect(req.request.params.get('hasta')).toBe('2026-08-16');
    expect(req.request.params.get('granularidad')).toBe('mes');
    expect(req.request.params.get('comparacion')).toBe('ninguna');
    expect(req.request.params.get('umbral_muestra')).toBeNull();
    req.flush({ data: [], meta: {} });
  });

  it('un_solo_metodo_obtener', () => {
    expect((api as unknown as { tiempoRespuestaGlobal?: unknown }).tiempoRespuestaGlobal).toBeUndefined();
  });

  it('no_llama_slugs_oe3', () => {
    const serial = JSON.stringify(api);
    expect(serial).not.toContain('latencia-asignacion');
    expect(serial).not.toContain('/oe3/');
  });
});
