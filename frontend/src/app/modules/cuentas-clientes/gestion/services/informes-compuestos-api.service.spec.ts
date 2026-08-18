/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { InformesCompuestosApiService } from './informes-compuestos-api.service';

describe('InformesCompuestosApiService (Cuentas)', () => {
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

  it('obtener_when_se_pide_incluye_slug_y_periodo_en_cuentas', () => {
    api.obtener('churn-por-cohorte', { desde: '2026-08-01', hasta: '2026-08-16' }).subscribe();

    const req = http.expectOne(
      (r) => r.url === '/api/v1/informes-tacticos/cuentas/churn-por-cohorte',
    );
    expect(req.request.url).not.toContain('/partners/');
    expect(req.request.url).not.toContain('/suscripciones/');
    expect(req.request.params.get('desde')).toBe('2026-08-01');
    expect(req.request.params.get('hasta')).toBe('2026-08-16');
    expect(req.request.params.get('dias_inactividad')).toBeNull();
    expect(req.request.params.get('mes_cohorte')).toBeNull();
    expect(req.request.params.get('pares_incompatibles')).toBeNull();
    req.flush({ data: { resultados: [] }, meta: {} });
  });

  it('no_expone_un_metodo_por_informe', () => {
    expect((api as unknown as { churnPorCohorte?: unknown }).churnPorCohorte).toBeUndefined();
    expect((api as unknown as { embudoAbandono?: unknown }).embudoAbandono).toBeUndefined();
  });
});
