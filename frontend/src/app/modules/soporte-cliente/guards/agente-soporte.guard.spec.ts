/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { agenteSoporteGuard } from './agente-soporte.guard';
import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

describe('agenteSoporteGuard', () => {
  it('allows_soporte_role', () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: (r: string) => r === 'Soporte' },
        },
        { provide: Router, useValue: { createUrlTree: () => false } },
      ],
    });
    const result = TestBed.runInInjectionContext(() => agenteSoporteGuard({} as never, {} as never));
    expect(result).toBe(true);
  });

  it('denies_cliente_role', () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: (r: string) => r === 'Cliente' },
        },
        { provide: Router, useValue: { createUrlTree: () => 'redirected' } },
      ],
    });
    const result = TestBed.runInInjectionContext(() => agenteSoporteGuard({} as never, {} as never));
    expect(result as unknown).toBe('redirected');
  });
});
