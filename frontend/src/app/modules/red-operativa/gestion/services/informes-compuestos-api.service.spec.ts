/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { InformesCompuestosApiService } from './informes-compuestos-api.service';

describe('InformesCompuestosApiService (Red Operativa)', () => {
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

  it('obtener_when_se_pide_incluye_slug_y_periodo_en_red_operativa', () => {
    api
      .obtener('condados-cobertura-critica', { desde: '2026-08-01', hasta: '2026-08-16' })
      .subscribe();

    const req = http.expectOne(
      (r) => r.url === '/api/v1/informes-tacticos/red-operativa/condados-cobertura-critica',
    );
    expect(req.request.url).not.toContain('/emergencias/');
    expect(req.request.params.get('desde')).toBe('2026-08-01');
    expect(req.request.params.get('hasta')).toBe('2026-08-16');
    expect(req.request.params.get('umbral_unidades')).toBeNull();
    req.flush({ data: [], meta: {} });
  });

  it('no_expone_un_metodo_por_informe', () => {
    expect((api as unknown as { unidadesPorEstado?: unknown }).unidadesPorEstado).toBeUndefined();
    expect((api as unknown as { motivosRechazo?: unknown }).motivosRechazo).toBeUndefined();
  });
});
