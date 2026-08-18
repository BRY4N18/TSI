/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { InformesCompuestosApiService } from './informes-compuestos-api.service';

describe('InformesCompuestosApiService (Partners)', () => {
  let api: InformesCompuestosApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(InformesCompuestosApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('obtener_when_se_pide_incluye_slug_y_periodo_en_partners', () => {
    api.obtener('latencia-p95', { desde: '2026-08-01', hasta: '2026-08-16' }).subscribe();

    const req = http.expectOne(
      (r) => r.url === '/api/v1/informes-tacticos/partners/latencia-p95',
    );
    expect(req.request.url).not.toContain('/soporte/');
    expect(req.request.url).not.toContain('/suscripciones/');
    expect(req.request.params.get('desde')).toBe('2026-08-01');
    expect(req.request.params.get('hasta')).toBe('2026-08-16');
    expect(req.request.params.get('percentil')).toBeNull();
    expect(req.request.params.get('muestra_minima')).toBeNull();
    expect(req.request.params.get('mes')).toBeNull();
    req.flush({ data: { resultados: [] }, meta: {} });
  });

  it('no_expone_un_metodo_por_informe', () => {
    expect((api as unknown as { latenciaP95?: unknown }).latenciaP95).toBeUndefined();
    expect((api as unknown as { comparativa?: unknown }).comparativa).toBeUndefined();
  });
});
