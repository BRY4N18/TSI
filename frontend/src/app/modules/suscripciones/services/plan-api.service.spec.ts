import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { PlanApiService } from './plan-api.service';

describe('PlanApiService', () => {
  let api: PlanApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
    });
    api = TestBed.inject(PlanApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('listar_envia_query_params_paginados', () => {
    api.listar({ cursor: 5, limit: 20, q: 'Pro', activo: true, nivel: 'Profesional' }).subscribe();
    const req = http.expectOne((r) => r.url === '/api/v1/suscripciones/planes');
    expect(req.request.params.get('cursor')).toBe('5');
    expect(req.request.params.get('limit')).toBe('20');
    expect(req.request.params.get('q')).toBe('Pro');
    expect(req.request.params.get('activo')).toBe('true');
    expect(req.request.params.get('nivel')).toBe('Profesional');
    req.flush({
      data: [],
      meta: { pagination: { next_cursor: null, limit: 20 } },
    });
  });

  it('listar_envia_solo_activos_false_para_todas', () => {
    api.listar({ limit: 20, solo_activos: false }).subscribe();
    const req = http.expectOne((r) => r.url === '/api/v1/suscripciones/planes');
    expect(req.request.params.get('solo_activos')).toBe('false');
    expect(req.request.params.get('activo')).toBeNull();
    req.flush({
      data: [],
      meta: { pagination: { next_cursor: null, limit: 20 } },
    });
  });

  it('buscarPorId_recorre_paginas_hasta_encontrar', () => {
    let foundId: number | undefined;
    api.buscarPorId(3).subscribe((p) => {
      foundId = p?.idplan;
    });

    const r1 = http.expectOne((r) => r.url === '/api/v1/suscripciones/planes');
    expect(r1.request.params.get('limit')).toBe('100');
    r1.flush({
      data: [{ idplan: 1, nombre: 'A' }],
      meta: { pagination: { next_cursor: 1, limit: 100 } },
    });

    const r2 = http.expectOne((r) => r.url === '/api/v1/suscripciones/planes');
    expect(r2.request.params.get('cursor')).toBe('1');
    r2.flush({
      data: [{ idplan: 3, nombre: 'C' }],
      meta: { pagination: { next_cursor: null, limit: 100 } },
    });

    expect(foundId).toBe(3);
  });
});
