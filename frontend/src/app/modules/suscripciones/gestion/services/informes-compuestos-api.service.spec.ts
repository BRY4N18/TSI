/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { InformesCompuestosApiService } from './informes-compuestos-api.service';

describe('InformesCompuestosApiService (Suscripciones)', () => {
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

  it('obtener_when_se_pide_incluye_slug_y_periodo_en_suscripciones', () => {
    api.obtener('mrr', { desde: '2026-08-01', hasta: '2026-08-16' }).subscribe();

    const req = http.expectOne((r) => r.url === '/api/v1/informes-tacticos/suscripciones/mrr');
    expect(req.request.url).not.toContain('/emergencias/');
    expect(req.request.url).not.toContain('/ventas-crm/');
    expect(req.request.params.get('desde')).toBe('2026-08-01');
    expect(req.request.params.get('hasta')).toBe('2026-08-16');
    expect(req.request.params.get('escalones_dunning')).toBeNull();
    expect(req.request.params.get('dias_aviso_caducidad')).toBeNull();
    expect(req.request.params.get('mes')).toBeNull();
    req.flush({ data: [], meta: {} });
  });

  it('no_expone_un_metodo_por_informe', () => {
    expect((api as unknown as { mrr?: unknown }).mrr).toBeUndefined();
    expect((api as unknown as { nrr?: unknown }).nrr).toBeUndefined();
  });
});
