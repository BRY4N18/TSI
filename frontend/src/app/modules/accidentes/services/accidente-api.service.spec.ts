/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { AccidenteApiService } from './accidente-api.service';

describe('AccidenteApiService', () => {
  let service: AccidenteApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [AccidenteApiService],
    });
    service = TestBed.inject(AccidenteApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('listar_when_ok_returns_envelope', () => {
    // Arrange
    const mock = { data: [{ idaccidente: 'ACC-1', idseveridad: 2, descripcion: 'x', activo: true }], meta: { pagination: { next_cursor: null, limit: 20 } } };

    // Act
    service.listar().subscribe((res) => expect(res.data.length).toBe(1));

    // Assert
    const req = http.expectOne('/api/v1/accidentes?limit=20');
    expect(req.request.method).toBe('GET');
    req.flush(mock);
  });

  it('detalle_when_ok_returns_envelope', () => {
    // Act
    service.detalle('ACC-1').subscribe((res) => expect(res.data.idaccidente).toBe('ACC-1'));

    // Assert
    const req = http.expectOne('/api/v1/accidentes/ACC-1');
    expect(req.request.method).toBe('GET');
    req.flush({ data: { idaccidente: 'ACC-1', historial_estados: [], ubicacion: {}, idseveridad: 2, descripcion: '', activo: true }, meta: { pagination: null } });
  });

  it('actualizar_when_ok_patches', () => {
    // Act
    service.actualizar('ACC-1', { numvehiculos: 3 }).subscribe();

    // Assert
    const req = http.expectOne('/api/v1/accidentes/ACC-1');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ numvehiculos: 3 });
    req.flush({ data: { message: 'ok', idaccidente: 'ACC-1', campos_modificados: ['numvehiculos'] }, meta: { pagination: null } });
  });
});
