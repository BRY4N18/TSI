/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';
import { unidadEmergenciaGuard } from './unidad-emergencia.guard';

describe('unidadEmergenciaGuard', () => {
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

  it('allows access when user has Unidad role', () => {
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasRole.and.returnValue(true);
    const result = TestBed.runInInjectionContext(() => unidadEmergenciaGuard({} as never, {} as never));
    expect(result).toBeTrue();
    expect(authApi.hasRole).toHaveBeenCalledWith('Unidad');
  });

  it('redirects when user lacks Unidad role', () => {
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasRole.and.returnValue(false);
    const result = TestBed.runInInjectionContext(() => unidadEmergenciaGuard({} as never, {} as never));
    expect(result).toEqual(router.createUrlTree(['/cuentas-clientes/auth/access-denied']));
  });
});
