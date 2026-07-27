import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { DemoApiService } from './demo-api.service';

describe('DemoApiService', () => {
  let service: DemoApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(DemoApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('abrirSesion posts to demo/sesiones', () => {
    service.abrirSesion({ idprospecto: 1, demo_grant: 'g' }).subscribe((res) => {
      expect(res.data.idprospecto).toBe(1);
    });
    const req = http.expectOne('/api/v1/ventas-crm/demo/sesiones');
    expect(req.request.method).toBe('POST');
    req.flush({
      data: {
        idprospecto: 1,
        demo_session_token: 't',
        demo_expiracion: '2026-07-25T00:00:00Z',
        modo: 'primer_canje',
      },
    });
  });
});
