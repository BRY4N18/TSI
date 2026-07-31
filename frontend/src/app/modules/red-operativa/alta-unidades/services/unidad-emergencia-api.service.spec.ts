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
        idcondado: 1,
        tipopropiedad: 'Externa',
        placa: 'ABC-123',
        contactoproveedor: '5551234',
        unidademergencia: 'Ambulancia Norte',
        tipounidademergencia: 'Ambulancia',
        gmail: 'unidad@test.com',
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

  it('listar_when_params_sends_query_and_reads_pagination', () => {
    const mock = {
      data: { items: [] },
      meta: { pagination: { next_cursor: 42, limit: 20 } },
    };

    service
      .listar({ cursor: 10, limit: 20, q: 'ABC', activo: true, tipounidademergencia: 'Ambulancia' })
      .subscribe((res) => {
        expect(res.meta.pagination?.next_cursor).toBe(42);
        expect(res.meta.pagination?.limit).toBe(20);
      });

    const req = http.expectOne(
      (r) =>
        r.url === '/api/v1/red-operativa/unidades' &&
        r.params.get('cursor') === '10' &&
        r.params.get('limit') === '20' &&
        r.params.get('q') === 'ABC' &&
        r.params.get('activo') === 'true' &&
        r.params.get('tipounidademergencia') === 'Ambulancia',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mock);
  });
});
