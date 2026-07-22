/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { SlaConfigApiService } from './sla-config-api.service';

describe('SlaConfigApiService', () => {
  let service: SlaConfigApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [SlaConfigApiService],
    });
    service = TestBed.inject(SlaConfigApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('listar_when_ok_returns_items', () => {
    service.listar().subscribe((res) => {
      expect(res.data.items.length).toBe(1);
    });
    const req = http.expectOne('/api/v1/soporte/sla-config');
    req.flush({ data: { items: [{ idslaconfig: 1 }] }, meta: {} });
  });

  it('modificar_when_ok_returns_nueva_regla', () => {
    service.modificar(1, 1800, 43200).subscribe((res) => {
      expect(res.data.tiemporespuestamax).toBe(1800);
    });
    const req = http.expectOne('/api/v1/soporte/sla-config/1');
    expect(req.request.method).toBe('PATCH');
    req.flush({ data: { idslaconfig: 2, tiemporespuestamax: 1800 }, meta: {} });
  });
});
