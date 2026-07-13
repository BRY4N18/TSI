/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';
import { clienteExpedienteGuard } from './cliente-expediente.guard';
import { operadorSeguimientoGuard } from './operador-seguimiento.guard';
import { unidadSeguimientoGuard } from './unidad-seguimiento.guard';

describe('seguimiento guards', () => {
  let authApi: jasmine.SpyObj<AuthApiService>;
  let router: Router;

  beforeEach(() => {
    authApi = jasmine.createSpyObj<AuthApiService>('AuthApiService', [
      'isAuthenticated',
      'hasAnyRole',
      'hasRole',
    ]);

    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      providers: [{ provide: AuthApiService, useValue: authApi }],
    });

    router = TestBed.inject(Router);
  });

  it('operadorSeguimientoGuard allows Operador roles', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasAnyRole.and.returnValue(true);

    // Act
    const result = TestBed.runInInjectionContext(() =>
      operadorSeguimientoGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toBeTrue();
  });

  it('unidadSeguimientoGuard redirects non-Unidad users', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasRole.and.returnValue(false);

    // Act
    const result = TestBed.runInInjectionContext(() =>
      unidadSeguimientoGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toEqual(router.createUrlTree(['/cuentas-clientes/auth/access-denied']));
  });

  it('clienteExpedienteGuard allows Cliente role', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasRole.and.returnValue(true);

    // Act
    const result = TestBed.runInInjectionContext(() =>
      clienteExpedienteGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toBeTrue();
  });

  it('operadorSeguimientoGuard redirects unauthenticated users', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(false);

    // Act
    const result = TestBed.runInInjectionContext(() =>
      operadorSeguimientoGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toEqual(router.createUrlTree(['/cuentas-clientes/auth/login']));
  });
});
