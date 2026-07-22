/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { clienteSoporteGuard } from './cliente-soporte.guard';
import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

describe('clienteSoporteGuard', () => {
  it('allows_cliente_role', () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: (r: string) => r === 'Cliente' },
        },
        { provide: Router, useValue: { createUrlTree: () => false } },
      ],
    });
    const result = TestBed.runInInjectionContext(() => clienteSoporteGuard({} as never, {} as never));
    expect(result).toBe(true);
  });

  it('denies_unidad_role', () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: (r: string) => r === 'Unidad' },
        },
        { provide: Router, useValue: { createUrlTree: () => 'redirected' } },
      ],
    });
    const result = TestBed.runInInjectionContext(() => clienteSoporteGuard({} as never, {} as never));
    expect(result as unknown).toBe('redirected');
  });
});
