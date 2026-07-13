/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';
import { operadorEmergenciasGuard } from './operador-emergencias.guard';

describe('operadorEmergenciasGuard', () => {
  let authApi: jasmine.SpyObj<AuthApiService>;
  let router: Router;

  beforeEach(() => {
    authApi = jasmine.createSpyObj<AuthApiService>('AuthApiService', [
      'isAuthenticated',
      'hasRole',
    ]);

    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      providers: [{ provide: AuthApiService, useValue: authApi }],
    });

    router = TestBed.inject(Router);
  });

  it('redirects unauthenticated users to login', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(false);

    // Act
    const result = TestBed.runInInjectionContext(() => operadorEmergenciasGuard({} as never, {} as never));

    // Assert
    expect(result).toEqual(router.createUrlTree(['/cuentas-clientes/auth/login']));
  });

  it('redirects users without Operador role to access denied', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasRole.and.returnValue(false);

    // Act
    const result = TestBed.runInInjectionContext(() => operadorEmergenciasGuard({} as never, {} as never));

    // Assert
    expect(result).toEqual(router.createUrlTree(['/cuentas-clientes/auth/access-denied']));
    expect(authApi.hasRole).toHaveBeenCalledWith('Operador');
  });

  it('allows access when user has Operador role', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasRole.and.returnValue(true);

    // Act
    const result = TestBed.runInInjectionContext(() => operadorEmergenciasGuard({} as never, {} as never));

    // Assert
    expect(result).toBeTrue();
  });
});
