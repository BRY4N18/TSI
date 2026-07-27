import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { NotificacionApiService } from './notificacion-api.service';

describe('NotificacionApiService', () => {
  let service: NotificacionApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(NotificacionApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('listar gets notificaciones', () => {
    service.listar({ limit: 10 }).subscribe((res) => {
      expect(res.data.length).toBe(0);
    });
    const req = http.expectOne((r) => r.url === '/api/v1/ventas-crm/notificaciones');
    expect(req.request.method).toBe('GET');
    req.flush({ data: [], meta: { pagination: { limit: 10, next_cursor: null } } });
  });
});
