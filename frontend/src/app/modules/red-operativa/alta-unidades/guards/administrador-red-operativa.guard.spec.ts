/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { administradorRedOperativaGuard } from './administrador-red-operativa.guard';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

describe('administradorRedOperativaGuard', () => {
  it('allows_administrador_role', () => {
    // Arrange
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: (r: string) => r === 'Administrador' },
        },
        { provide: Router, useValue: { createUrlTree: () => false } },
      ],
    });

    // Act
    const result = TestBed.runInInjectionContext(() =>
      administradorRedOperativaGuard({} as never, {} as never),
    );

    // Assert
    expect(result).toBe(true);
  });

  it('blocks_operador_role', () => {
    // Arrange
    let redirected = false;
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: (r: string) => r === 'Operador' },
        },
        { provide: Router, useValue: { createUrlTree: () => (redirected = true) } },
      ],
    });

    // Act
    TestBed.runInInjectionContext(() => administradorRedOperativaGuard({} as never, {} as never));

    // Assert
    expect(redirected).toBe(true);
  });

  it('blocks_unauthenticated', () => {
    // Arrange
    let redirected = false;
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => false, hasRole: () => false },
        },
        { provide: Router, useValue: { createUrlTree: () => (redirected = true) } },
      ],
    });

    // Act
    TestBed.runInInjectionContext(() => administradorRedOperativaGuard({} as never, {} as never));

    // Assert
    expect(redirected).toBe(true);
  });
});
