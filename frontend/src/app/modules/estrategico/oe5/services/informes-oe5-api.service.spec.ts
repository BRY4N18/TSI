/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { InformesOe5ApiService } from './informes-oe5-api.service';

describe('InformesOe5ApiService', () => {
  let api: InformesOe5ApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(InformesOe5ApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('obtener_usa_prefijo_oe5_y_cuatro_params', () => {
    api
      .obtener('cumplimiento-sla', {
        desde: '2026-08-01',
        hasta: '2026-08-16',
        granularidad: 'mes',
        comparacion: 'ninguna',
      })
      .subscribe();

    const req = http.expectOne((r) => r.url === '/api/v1/informes-estrategicos/oe5/cumplimiento-sla');
    expect(req.request.url).not.toContain('informes-tacticos');
    expect(req.request.url).not.toContain('/oe1/');
    expect(req.request.params.get('desde')).toBe('2026-08-01');
    expect(req.request.params.get('hasta')).toBe('2026-08-16');
    expect(req.request.params.get('granularidad')).toBe('mes');
    expect(req.request.params.get('comparacion')).toBe('ninguna');
    expect(req.request.params.get('umbral_muestra')).toBeNull();
    req.flush({ data: [], meta: {} });
  });

  it('un_solo_metodo_obtener', () => {
    expect((api as unknown as { cumplimientoSla?: unknown }).cumplimientoSla).toBeUndefined();
  });

  it('no_llama_slugs_bloqueados', () => {
    const serial = JSON.stringify(api);
    expect(serial).not.toContain('nps-satisfaccion');
    expect(serial).not.toContain('reportes-sin-correccion');
    expect(serial).not.toContain('tasa-renovacion');
  });
});
