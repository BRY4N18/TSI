/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';
import { adminBillingGuard } from './admin-billing.guard';

describe('adminBillingGuard', () => {
  it('allows Administrador role when authenticated', () => {
    // Arrange
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: {
            isAuthenticated: () => true,
            hasRole: (r: string) => r === 'Administrador',
          },
        },
        { provide: Router, useValue: { createUrlTree: () => false } },
      ],
    });
    // Act
    const result = TestBed.runInInjectionContext(() =>
      adminBillingGuard({} as never, {} as never),
    );
    // Assert
    expect(result).toBe(true);
  });

  it('denies non-admin roles', () => {
    // Arrange
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: () => false },
        },
        { provide: Router, useValue: { createUrlTree: () => 'redirected' } },
      ],
    });
    // Act
    const result = TestBed.runInInjectionContext(() =>
      adminBillingGuard({} as never, {} as never),
    );
    // Assert
    expect(result as unknown).toBe('redirected');
  });
});
