/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { operadorDespachoGuard } from './operador-despacho.guard';
import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

describe('operadorDespachoGuard', () => {
  it('allows_operador_role', () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: (r: string) => r === 'Operador' },
        },
        { provide: Router, useValue: { createUrlTree: () => false } },
      ],
    });
    const result = TestBed.runInInjectionContext(() => operadorDespachoGuard({} as never, {} as never));
    expect(result).toBe(true);
  });
});
