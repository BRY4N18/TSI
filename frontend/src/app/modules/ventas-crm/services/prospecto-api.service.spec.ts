/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { ProspectoApiService } from './prospecto-api.service';

describe('ProspectoApiService', () => {
  let service: ProspectoApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
    });
    service = TestBed.inject(ProspectoApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('listar_calls_get_prospectos', () => {
    // Arrange
    let result: unknown;
    // Act
    service.listar({ limit: 20 }).subscribe((r) => (result = r));
    const req = httpMock.expectOne('/api/v1/ventas-crm/prospectos?limit=20');
    req.flush({ data: [], meta: {} });
    // Assert
    expect(req.request.method).toBe('GET');
    expect(result).toEqual({ data: [], meta: {} });
  });

  it('listar_envia_filtros_y_cursor', () => {
    service
      .listar({ cursor: 5, limit: 20, activo: false, etapa_actual: 'Negociación' })
      .subscribe();
    const req = httpMock.expectOne((r) => r.url === '/api/v1/ventas-crm/prospectos');
    expect(req.request.params.get('limit')).toBe('20');
    expect(req.request.params.get('cursor')).toBe('5');
    expect(req.request.params.get('activo')).toBe('false');
    expect(req.request.params.get('etapa_actual')).toBe('Negociación');
    req.flush({ data: [], meta: { pagination: { next_cursor: null, limit: 20 } } });
  });
});
