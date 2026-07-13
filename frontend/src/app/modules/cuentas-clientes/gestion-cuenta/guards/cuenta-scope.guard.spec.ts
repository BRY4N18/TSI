import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot } from '@angular/router';
import { of } from 'rxjs';

import { AuthApiService } from '../../auth/services/auth-api.service';
import { CuentaClienteApiService } from '../services/cuenta-cliente-api.service';
import { cuentaScopeGuard } from './cuenta-scope.guard';

describe('CuentaScopeGuard', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        { provide: Router, useValue: { createUrlTree: () => '/login' } },
        {
          provide: AuthApiService,
          useValue: {
            getProfile: () => ({ idusuario: 3, gmail: 'c@test.com', roles: ['Cliente'] }),
          },
        },
        {
          provide: CuentaClienteApiService,
          useValue: {
            getPerfil: () =>
              of({
                data: { idcliente: 1, estado: 'Activo' },
                meta: { pagination: null },
              }),
          },
        },
      ],
    });
  });

  it('allows_admin_for_any_cliente', () => {
    // Arrange
    TestBed.overrideProvider(AuthApiService, {
      useValue: {
        getProfile: () => ({ idusuario: 1, gmail: 'a@test.com', roles: ['Administrador'] }),
      },
    });
    const route = { paramMap: { get: () => '1' } } as unknown as ActivatedRouteSnapshot;

    // Act
    const result = TestBed.runInInjectionContext(() =>
      cuentaScopeGuard(route, {} as RouterStateSnapshot),
    );

    // Assert
    expect(result).toBeTrue();
  });
});
