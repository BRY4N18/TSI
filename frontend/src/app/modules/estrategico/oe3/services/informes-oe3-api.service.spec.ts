/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { BLOQUEADOS_UI } from '../definiciones/pantallas-oe3.definiciones';
import { InformesOe3ApiService } from './informes-oe3-api.service';

describe('InformesOe3ApiService', () => {
  let api: InformesOe3ApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(InformesOe3ApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('obtener_usa_prefijo_oe3_y_cuatro_params', () => {
    api
      .obtener('latencia-asignacion', {
        desde: '2026-08-01',
        hasta: '2026-08-16',
        granularidad: 'mes',
        comparacion: 'ninguna',
      })
      .subscribe();

    const req = http.expectOne(
      (r) => r.url === '/api/v1/informes-estrategicos/oe3/latencia-asignacion',
    );
    expect(req.request.url).not.toContain('informes-tacticos');
    expect(req.request.url).not.toContain('/oe6/');
    expect(req.request.params.get('desde')).toBe('2026-08-01');
    expect(req.request.params.get('hasta')).toBe('2026-08-16');
    expect(req.request.params.get('granularidad')).toBe('mes');
    expect(req.request.params.get('comparacion')).toBe('ninguna');
    expect(req.request.params.get('umbral_seg')).toBeNull();
    expect(req.request.params.get('umbral_muestra')).toBeNull();
    req.flush({ data: [], meta: {} });
  });

  it('un_solo_metodo_obtener', () => {
    expect((api as unknown as { latenciaAsignacion?: unknown }).latenciaAsignacion).toBeUndefined();
  });

  it('no_llama_slugs_bloqueados_ni_oe6', () => {
    const serial = JSON.stringify(api);
    for (const slug of BLOQUEADOS_UI) {
      expect(serial).not.toContain(slug);
    }
    expect(serial).not.toContain('/oe6/');
  });
});
