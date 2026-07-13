/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { ExpedienteClienteApiService } from './expediente-cliente-api.service';

describe('ExpedienteClienteApiService', () => {
  let service: ExpedienteClienteApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ExpedienteClienteApiService],
    });
    service = TestBed.inject(ExpedienteClienteApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('listar_when_ok_returns_items', () => {
    // Arrange
    const mock = {
      data: { items: [], next_cursor: null },
      meta: { timestamp: '2026-07-09T00:00:00Z' },
    };

    // Act
    service.listar().subscribe((res) => {
      // Assert
      expect(res.data.items).toEqual([]);
    });

    const req = http.expectOne('/api/v1/cliente/expedientes');
    expect(req.request.method).toBe('GET');
    req.flush(mock);
  });

  it('descargarPdf_when_ok_returns_blob', () => {
    // Arrange
    const blob = new Blob(['%PDF'], { type: 'application/pdf' });

    // Act
    service.descargarPdf('ACC-1').subscribe((res) => {
      // Assert
      expect(res.type).toBe('application/pdf');
    });

    const req = http.expectOne('/api/v1/cliente/expedientes/ACC-1/pdf');
    expect(req.request.responseType).toBe('blob');
    req.flush(blob);
  });
});
