/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { MiDespachoApiService } from './mi-despacho-api.service';

describe('MiDespachoApiService', () => {
  let service: MiDespachoApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [MiDespachoApiService],
    });
    service = TestBed.inject(MiDespachoApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('listarPendientes_when_ok_returns_list', () => {
    service.listarPendientes().subscribe((res) => {
      expect(res.data.pendientes.length).toBe(1);
    });
    const req = http.expectOne('/api/v1/mi-despacho/pendientes');
    req.flush({ data: { pendientes: [{ idnotificaciondespacho: 1 }] }, meta: {} });
  });
});
