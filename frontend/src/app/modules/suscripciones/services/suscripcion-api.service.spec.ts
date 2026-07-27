/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { SuscripcionApiService } from './suscripcion-api.service';

describe('SuscripcionApiService', () => {
  let service: SuscripcionApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
    });
    service = TestBed.inject(SuscripcionApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('obtenerMiSuscripcion_calls_get_mia', () => {
    // Arrange
    let result: unknown;
    // Act
    service.obtenerMiSuscripcion().subscribe((r) => (result = r));
    const req = httpMock.expectOne('/api/v1/suscripciones/mia');
    req.flush({ data: { estado: 'Activa' }, meta: {} });
    // Assert
    expect(req.request.method).toBe('GET');
    expect(result).toEqual({ data: { estado: 'Activa' }, meta: {} });
  });
});
