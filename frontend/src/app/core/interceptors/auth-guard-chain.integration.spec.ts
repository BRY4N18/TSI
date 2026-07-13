/** @marker integration */
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AUTH_STORAGE_KEYS } from '../../modules/cuentas-clientes/auth/services/auth-api.types';
import { roleGuard } from '../../modules/cuentas-clientes/auth/guards/role.guard';
import { sessionGuard } from '../../modules/cuentas-clientes/auth/guards/session.guard';
import { authInterceptor } from './auth.interceptor';

describe('sessionGuard -> roleGuard -> authInterceptor chain', () => {
  let router: Router;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();

    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });

    router = TestBed.inject(Router);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  function runGuards(routeData: Record<string, unknown>, url: string) {
    return TestBed.runInInjectionContext(() => {
      const route = { data: routeData } as unknown as ActivatedRouteSnapshot;
      const state = { url } as RouterStateSnapshot;

      const sessionResult = sessionGuard(route, state);
      if (sessionResult !== true) {
        return sessionResult;
      }
      return roleGuard(route, state);
    });
  }

  it('unauthenticated_user_is_redirected_to_login_before_reaching_roleGuard', () => {
    // Act
    const result = runGuards({ roles: ['Administrador'] }, '/cuentas-clientes/admin');

    // Assert
    expect(result).toEqual(
      router.createUrlTree(['/cuentas-clientes/auth/login'], {
        queryParams: { returnUrl: '/cuentas-clientes/admin' },
      }),
    );
  });

  it('authenticated_user_without_required_role_is_denied_by_roleGuard', () => {
    // Arrange
    localStorage.setItem(AUTH_STORAGE_KEYS.accessToken, 'access-token');
    localStorage.setItem(
      AUTH_STORAGE_KEYS.profile,
      JSON.stringify({ idusuario: 1, gmail: 'user@test.com', roles: ['Operador'] }),
    );
    localStorage.setItem(AUTH_STORAGE_KEYS.requiresPasswordChange, 'false');

    // Act
    const result = runGuards({ roles: ['Administrador'] }, '/cuentas-clientes/admin');

    // Assert
    expect(result).toEqual(router.createUrlTree(['/cuentas-clientes/auth/access-denied']));
  });

  it('authorized_user_passes_the_chain_and_authInterceptor_attaches_bearer_token', () => {
    // Arrange
    localStorage.setItem(AUTH_STORAGE_KEYS.accessToken, 'access-token');
    localStorage.setItem(
      AUTH_STORAGE_KEYS.profile,
      JSON.stringify({ idusuario: 1, gmail: 'admin@test.com', roles: ['Administrador'] }),
    );
    localStorage.setItem(AUTH_STORAGE_KEYS.requiresPasswordChange, 'false');

    // Act
    const result = runGuards({ roles: ['Administrador'] }, '/cuentas-clientes/admin');

    // Assert: guard chain allows navigation
    expect(result).toBeTrue();

    // Assert: any subsequent HTTP call carries the bearer token via the real interceptor
    const http = TestBed.inject(HttpClient);
    http.get('/api/v1/usuarios').subscribe();
    const req = httpMock.expectOne('/api/v1/usuarios');
    expect(req.request.headers.get('Authorization')).toBe('Bearer access-token');
    req.flush({ data: [], meta: {} });
  });
});
