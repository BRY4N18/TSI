/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';
import { evidenciaGalleryGuard } from './evidencia-gallery.guard';

describe('evidenciaGalleryGuard', () => {
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

  it('redirects unauthenticated users to login', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(false);

    // Act
    const result = TestBed.runInInjectionContext(() =>
      evidenciaGalleryGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toEqual(router.createUrlTree(['/cuentas-clientes/auth/login']));
  });

  it('allows gallery roles', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.hasAnyRole.and.returnValue(true);

    // Act
    const result = TestBed.runInInjectionContext(() =>
      evidenciaGalleryGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toBeTrue();
  });
});
