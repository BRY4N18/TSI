/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';
import { proveedorBillingGuard } from './proveedor-billing.guard';

describe('proveedorBillingGuard', () => {
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

  it('allows Proveedor role when authenticated', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasRole.and.callFake((role: string) => role === 'Proveedor');
    // Act
    const result = TestBed.runInInjectionContext(() =>
      proveedorBillingGuard({} as never, {} as never),
    );
    // Assert
    expect(result).toBe(true);
  });

  it('denies when neither Cliente nor Proveedor', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasRole.and.returnValue(false);
    router.createUrlTree.and.returnValue('/denied' as never);
    // Act
    const result = TestBed.runInInjectionContext(() =>
      proveedorBillingGuard({} as never, {} as never),
    );
    // Assert
    expect(result).not.toBe(true);
    expect(router.createUrlTree).toHaveBeenCalledWith(['/cuentas-clientes/auth/access-denied']);
  });
});
