/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { PlanesApiService } from './planes-api.service';

describe('PlanesApiService', () => {
  let service: PlanesApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
    });
    service = TestBed.inject(PlanesApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('listar_calls_get_planes_sin_auth_headers', () => {
    // Arrange
    let result: unknown;
    // Act
    service.listar().subscribe((r) => (result = r));
    const req = httpMock.expectOne('/api/v1/ventas-crm/planes');
    req.flush({
      data: [
        {
          idplan: 2,
          nombre: 'Profesional',
          precio: 149,
          limites: '{}',
          nivel: 'Profesional',
          severidades_desbloqueadas: ['Baja', 'Media'],
        },
      ],
    });
    // Assert
    expect(req.request.method).toBe('GET');
    expect(result).toEqual({
      data: [
        {
          idplan: 2,
          nombre: 'Profesional',
          precio: 149,
          limites: '{}',
          nivel: 'Profesional',
          severidades_desbloqueadas: ['Baja', 'Media'],
        },
      ],
    });
  });
});
