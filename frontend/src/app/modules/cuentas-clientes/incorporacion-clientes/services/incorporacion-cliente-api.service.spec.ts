import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { IncorporacionClienteApiService } from './incorporacion-cliente-api.service';

describe('IncorporacionClienteApiService', () => {
  let service: IncorporacionClienteApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [IncorporacionClienteApiService],
    });
    service = TestBed.inject(IncorporacionClienteApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('registrarCuenta_when_ok_returns_envelope', () => {
    // Arrange
    const payload = {
      razon_social: 'Acme SA',
      nombre: 'Acme',
      tipo: 'Aseguradora' as const,
      nit_identificacion: '900123456',
      fecha_inicio_contrato: 1_700_000_000_000,
      admin_local: { nombres: 'Ana', apellidos: 'López', gmail: 'ana@acme.com' },
    };
    const mock = {
      data: {
        idcliente: 42,
        estado: 'Activo' as const,
        admin_local_id: 7,
        admin_local_gmail: 'ana@acme.com',
        message: 'Cuenta creada',
      },
      meta: { pagination: null },
    };

    // Act
    service.registrarCuenta(payload).subscribe((res) => {
      // Assert
      expect(res.data.idcliente).toBe(42);
      expect(res.data.estado).toBe('Activo');
    });

    const req = http.expectOne('/api/v1/cuentas-clientes');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(mock);
  });
});
