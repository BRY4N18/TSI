/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { ConversionApiService } from './conversion-api.service';

describe('ConversionApiService', () => {
  let service: ConversionApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(ConversionApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('convertir_sends_idempotency_key', () => {
    service
      .convertir(
        1,
        { tipo: 'Aseguradora', nit_identificacion: '1', etapa_actual_esperada: 'Negociación' },
        '11111111-1111-1111-1111-111111111111',
      )
      .subscribe();
    const req = httpMock.expectOne('/api/v1/ventas-crm/prospectos/1/conversion');
    expect(req.request.headers.get('Idempotency-Key')).toBe(
      '11111111-1111-1111-1111-111111111111',
    );
    req.flush({ data: {} });
  });

  it('entradaDirecta_posts_clientes', () => {
    service
      .entradaDirecta({
        nombre: 'X',
        razon_social: 'Y',
        tipo: 'Municipio',
        nit_identificacion: '99',
        admin_local: { nombres: 'Ana', apellidos: 'Admin', gmail: 'ana.admin@ex.com' },
      })
      .subscribe();
    const req = httpMock.expectOne('/api/v1/ventas-crm/clientes/entrada-directa');
    expect(req.request.method).toBe('POST');
    req.flush({ data: {} });
  });
});
