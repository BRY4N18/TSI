/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthApiService } from '../services/auth-api.service';
import { sessionGuard } from './session.guard';

describe('sessionGuard', () => {
  let authApi: jasmine.SpyObj<AuthApiService>;
  let router: Router;

  beforeEach(() => {
    authApi = jasmine.createSpyObj<AuthApiService>('AuthApiService', [
      'isAuthenticated',
      'requiresPasswordChange',
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
    const result = TestBed.runInInjectionContext(() =>
      sessionGuard({} as never, { url: '/cuentas-clientes/dashboard' } as never),
    );

    // Assert
    expect(result).toEqual(
      router.createUrlTree(['/cuentas-clientes/auth/login'], {
        queryParams: { returnUrl: '/cuentas-clientes/dashboard' },
      }),
    );
  });

  it('redirects to password reset when change is required', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.requiresPasswordChange.and.returnValue(true);

    // Act
    const result = TestBed.runInInjectionContext(() =>
      sessionGuard({} as never, { url: '/cuentas-clientes/dashboard' } as never),
    );

    // Assert
    expect(result).toEqual(
      router.createUrlTree(['/cuentas-clientes/auth/password-reset'], {
        queryParams: { forced: 'true' },
      }),
    );
  });

  it('allows access for authenticated users without forced password change', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.requiresPasswordChange.and.returnValue(false);

    // Act
    const result = TestBed.runInInjectionContext(() =>
      sessionGuard({} as never, { url: '/cuentas-clientes/dashboard' } as never),
    );

    // Assert
    expect(result).toBeTrue();
  });
});
