/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { InformesCompuestosApiService } from './informes-compuestos-api.service';

describe('InformesCompuestosApiService (Soporte al Cliente)', () => {
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

  it('obtener_when_se_pide_incluye_slug_y_periodo_en_soporte', () => {
    api
      .obtener('cumplimiento-sla', { desde: '2026-08-01', hasta: '2026-08-16' })
      .subscribe();

    const req = http.expectOne(
      (r) => r.url === '/api/v1/informes-tacticos/soporte/cumplimiento-sla',
    );
    expect(req.request.url).not.toContain('/ventas-crm/');
    expect(req.request.params.get('desde')).toBe('2026-08-01');
    expect(req.request.params.get('hasta')).toBe('2026-08-16');
    expect(req.request.params.get('granularidad')).toBeNull();
    expect(req.request.params.get('eje')).toBeNull();
    expect(req.request.params.get('minimo')).toBeNull();
    req.flush({ data: { resultados: [], declaraciones: [] }, meta: {} });
  });

  it('cumplimiento_por_plan_when_se_pide_usa_la_ruta_anidada', () => {
    api
      .obtener('cumplimiento-sla-por-plan', { desde: '2026-01-01', hasta: '2026-12-31' })
      .subscribe();

    const req = http.expectOne(
      (r) => r.url === '/api/v1/informes-tacticos/soporte/cumplimiento-sla/por-plan',
    );
    expect(req.request.url).not.toContain('cumplimiento-sla-por-plan');
    req.flush({ data: { resultados: [], declaraciones: [] }, meta: {} });
  });

  it('no_expone_un_metodo_por_informe', () => {
    expect((api as unknown as { cumplimientoSla?: unknown }).cumplimientoSla).toBeUndefined();
    expect((api as unknown as { tableroCola?: unknown }).tableroCola).toBeUndefined();
  });
});
