/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { InformesCompuestosApiService } from './informes-compuestos-api.service';

describe('InformesCompuestosApiService', () => {
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

  it('obtener_when_se_pide_incluye_slug_y_periodo', () => {
    api.obtener('completitud-campos-criticos', { desde: '2026-08-01', hasta: '2026-08-16' }).subscribe();

    const req = http.expectOne(
      (r) => r.url === '/api/v1/informes-tacticos/emergencias/completitud-campos-criticos',
    );
    expect(req.request.params.get('desde')).toBe('2026-08-01');
    expect(req.request.params.get('hasta')).toBe('2026-08-16');
    req.flush({ data: [], meta: {} });
  });

  it('no_expone_un_metodo_por_informe_vigilado', () => {
    expect((api as unknown as { distribucionSeveridad?: unknown }).distribucionSeveridad).toBeUndefined();
    expect((api as unknown as { cierresForzados?: unknown }).cierresForzados).toBeUndefined();
  });
});
