/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthApiService } from '../services/auth-api.service';
import { roleGuard } from './role.guard';

describe('roleGuard', () => {
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

  it('allows access when no roles are required', () => {
    // Arrange
    const route = { data: {} } as never;

    // Act
    const result = TestBed.runInInjectionContext(() => roleGuard(route, {} as never));

    // Assert
    expect(result).toBeTrue();
  });

  it('redirects unauthenticated users to login', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(false);
    const route = { data: { roles: ['Administrador'] } } as never;

    // Act
    const result = TestBed.runInInjectionContext(() => roleGuard(route, {} as never));

    // Assert
    expect(result).toEqual(router.createUrlTree(['/cuentas-clientes/auth/login']));
  });

  it('redirects users without required roles to access denied', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasAnyRole.and.returnValue(false);
    const route = { data: { roles: ['Administrador'] } } as never;

    // Act
    const result = TestBed.runInInjectionContext(() => roleGuard(route, {} as never));

    // Assert
    expect(result).toEqual(router.createUrlTree(['/cuentas-clientes/auth/access-denied']));
    expect(authApi.hasAnyRole).toHaveBeenCalledWith(['Administrador']);
  });

  it('allows access when user has a required role', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasAnyRole.and.returnValue(true);
    const route = { data: { roles: ['Administrador', 'Director Tecnológico'] } } as never;

    // Act
    const result = TestBed.runInInjectionContext(() => roleGuard(route, {} as never));

    // Assert
    expect(result).toBeTrue();
  });
});
