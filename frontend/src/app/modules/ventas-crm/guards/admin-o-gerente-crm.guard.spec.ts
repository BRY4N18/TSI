/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { adminOGerenteCrmGuard } from './admin-o-gerente-crm.guard';
import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

describe('adminOGerenteCrmGuard', () => {
  it('allows_gerente_ventas_role', () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: {
            isAuthenticated: () => true,
            hasRole: (r: string) => r === 'GerenteVentas',
          },
        },
        { provide: Router, useValue: { createUrlTree: () => false } },
      ],
    });
    const result = TestBed.runInInjectionContext(() =>
      adminOGerenteCrmGuard({} as never, {} as never),
    );
    expect(result).toBe(true);
  });

  it('denies_operador_role', () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: (r: string) => r === 'Operador' },
        },
        { provide: Router, useValue: { createUrlTree: () => 'redirected' } },
      ],
    });
    const result = TestBed.runInInjectionContext(() =>
      adminOGerenteCrmGuard({} as never, {} as never),
    );
    expect(result as unknown).toBe('redirected');
  });
});
