/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { UnidadEmergenciaApiService } from './unidad-emergencia-api.service';

describe('UnidadEmergenciaApiService', () => {
  let service: UnidadEmergenciaApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [UnidadEmergenciaApiService],
    });
    service = TestBed.inject(UnidadEmergenciaApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('registrar_when_ok_posts_to_unidades_endpoint', () => {
    // Arrange
    const mock = { data: { idunidademergencia: 500, placa: 'ABC-123', activo: true }, meta: { pagination: null } };

    // Act
    service
      .registrar({
        idcliente: 1,
        idcondado: 1,
        tipopropiedad: 'Externa',
        placa: 'ABC-123',
        contactoproveedor: '5551234',
        unidademergencia: 'Ambulancia Norte',
        tipounidademergencia: 'Ambulancia',
      })
      .subscribe((res) => {
        // Assert
        expect(res.data.idunidademergencia).toBe(500);
      });

    const req = http.expectOne('/api/v1/red-operativa/unidades');
    expect(req.request.method).toBe('POST');
    req.flush(mock);
  });

  it('obtener_when_ok_gets_unidad_by_id', () => {
    // Arrange
    const mock = {
      data: {
        idunidademergencia: 500,
        idcliente: 1,
        idcondado: 1,
        tipopropiedad: 'Externa' as const,
        placa: 'ABC-123',
        capacidad: null,
        contactoproveedor: null,
        unidademergencia: 'Ambulancia Norte',
        tipounidademergencia: 'Ambulancia' as const,
        activo: true,
        latitud: null,
        longitud: null,
      },
      meta: { pagination: null },
    };

    // Act
    service.obtener(500).subscribe((res) => {
      // Assert
      expect(res.data.placa).toBe('ABC-123');
    });

    const req = http.expectOne('/api/v1/red-operativa/unidades/500');
    expect(req.request.method).toBe('GET');
    req.flush(mock);
  });
});
