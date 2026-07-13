import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { CuentaClienteApiService } from './cuenta-cliente-api.service';

describe('CuentaClienteApiService', () => {
  let service: CuentaClienteApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [CuentaClienteApiService],
    });
    service = TestBed.inject(CuentaClienteApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('getPerfil_when_ok_returns_envelope', () => {
    // Arrange
    const mock = {
      data: { idcliente: 1, razon_social: 'Demo', nombre: 'Demo', tipo: 'Corp', nit_identificacion: '1', logo_url: null, estado: 'Activo' as const, admin_local_id: 3 },
      meta: { pagination: null },
    };

    // Act
    service.getPerfil(1).subscribe((res) => {
      // Assert
      expect(res.data.idcliente).toBe(1);
    });

    const req = http.expectOne('/api/v1/cuentas-clientes/1/perfil');
    expect(req.request.method).toBe('GET');
    req.flush(mock);
  });
});
