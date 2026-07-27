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

  it('autorregistrar_when_ok_returns_envelope', () => {
    // Arrange
    const payload = {
      razon_social: 'Acme SA',
      nombre: 'Acme',
      tipo: 'Proveedor' as const,
      nit_identificacion: '900123456',
      admin_local: { nombres: 'Ana', apellidos: 'López', gmail: 'ana@acme.com' },
    };
    const mock = {
      data: {
        idcliente: 42,
        estado: 'Pendiente_Aprobación' as const,
        admin_local_id: 7,
        admin_local_gmail: 'ana@acme.com',
        message: 'Solicitud en revisión',
      },
      meta: { pagination: null },
    };

    // Act
    service.autorregistrar(payload).subscribe((res) => {
      // Assert
      expect(res.data.idcliente).toBe(42);
      expect(res.data.estado).toBe('Pendiente_Aprobación');
    });

    const req = http.expectOne('/api/v1/cuentas-clientes/autorregistro');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(mock);
  });
});
