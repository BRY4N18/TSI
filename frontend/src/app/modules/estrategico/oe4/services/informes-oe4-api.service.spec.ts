/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { BLOQUEADOS_UI } from '../definiciones/pantallas-oe4.definiciones';
import { InformesOe4ApiService } from './informes-oe4-api.service';

describe('InformesOe4ApiService', () => {
  let api: InformesOe4ApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(InformesOe4ApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('obtener_usa_prefijo_oe4_y_cuatro_params', () => {
    api
      .obtener('indice-calidad-historico', {
        desde: '2026-08-01',
        hasta: '2026-08-16',
        granularidad: 'mes',
        comparacion: 'ninguna',
      })
      .subscribe();

    const req = http.expectOne(
      (r) => r.url === '/api/v1/informes-estrategicos/oe4/indice-calidad-historico',
    );
    expect(req.request.url).not.toContain('/oe3/');
    expect(req.request.params.get('desde')).toBe('2026-08-01');
    expect(req.request.params.get('granularidad')).toBe('mes');
    req.flush({ data: [], meta: {} });
  });

  it('un_solo_metodo_obtener', () => {
    expect((api as unknown as { indiceCalidad?: unknown }).indiceCalidad).toBeUndefined();
  });

  it('no_llama_slugs_bloqueados', () => {
    const serial = JSON.stringify(api);
    for (const slug of BLOQUEADOS_UI) {
      expect(serial).not.toContain(slug);
    }
  });
});
