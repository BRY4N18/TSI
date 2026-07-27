/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { proveedorFlotaGuard } from './proveedor-flota.guard';

describe('proveedorFlotaGuard', () => {
  let authApi: jasmine.SpyObj<AuthApiService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authApi = jasmine.createSpyObj('AuthApiService', ['isAuthenticated', 'hasRole']);
    router = jasmine.createSpyObj('Router', ['createUrlTree']);
    TestBed.configureTestingModule({
      providers: [
        { provide: AuthApiService, useValue: authApi },
        { provide: Router, useValue: router },
      ],
    });
  });

  it('allows Cliente role when authenticated', () => {
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasRole.and.callFake((role: string) => role === 'Cliente');

    const result = TestBed.runInInjectionContext(() => proveedorFlotaGuard({} as never, {} as never));

    expect(result).toBe(true);
  });

  it('denies Administrador (no override)', () => {
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasRole.and.returnValue(false);
    router.createUrlTree.and.returnValue('/denied' as never);

    const result = TestBed.runInInjectionContext(() => proveedorFlotaGuard({} as never, {} as never));

    expect(result).not.toBe(true);
    expect(router.createUrlTree).toHaveBeenCalled();
  });
});
