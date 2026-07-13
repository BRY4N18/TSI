/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';
import { administradorFlotaGuard } from './administrador-flota.guard';

describe('administradorFlotaGuard', () => {
  let authApi: jasmine.SpyObj<AuthApiService>;
  let router: Router;

  beforeEach(() => {
    authApi = jasmine.createSpyObj<AuthApiService>('AuthApiService', [
      'isAuthenticated',
      'hasAnyRole',
    ]);

    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      providers: [{ provide: AuthApiService, useValue: authApi }],
    });

    router = TestBed.inject(Router);
  });

  it('allows Administrador or Despacho roles', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasAnyRole.and.returnValue(true);

    // Act
    const result = TestBed.runInInjectionContext(() =>
      administradorFlotaGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toBeTrue();
  });

  it('redirects unauthorized users', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasAnyRole.and.returnValue(false);

    // Act
    const result = TestBed.runInInjectionContext(() =>
      administradorFlotaGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toEqual(router.createUrlTree(['/cuentas-clientes/auth/access-denied']));
  });
});
