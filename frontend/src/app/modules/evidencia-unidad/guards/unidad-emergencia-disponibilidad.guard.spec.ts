/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';
import { unidadEmergenciaDisponibilidadGuard } from './unidad-emergencia-disponibilidad.guard';

describe('unidadEmergenciaDisponibilidadGuard', () => {
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

  it('allows Unidad role', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasRole.and.returnValue(true);

    // Act
    const result = TestBed.runInInjectionContext(() =>
      unidadEmergenciaDisponibilidadGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toBeTrue();
    expect(authApi.hasRole).toHaveBeenCalledWith('Unidad');
  });

  it('redirects users without Unidad role', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasRole.and.returnValue(false);

    // Act
    const result = TestBed.runInInjectionContext(() =>
      unidadEmergenciaDisponibilidadGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toEqual(router.createUrlTree(['/cuentas-clientes/auth/access-denied']));
  });
});
