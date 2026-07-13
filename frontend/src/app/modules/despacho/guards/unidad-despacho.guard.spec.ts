/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { unidadDespachoGuard } from './unidad-despacho.guard';
import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

describe('unidadDespachoGuard', () => {
  it('allows_unidad_role', () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: (r: string) => r === 'Unidad' },
        },
        { provide: Router, useValue: { createUrlTree: () => false } },
      ],
    });
    const result = TestBed.runInInjectionContext(() => unidadDespachoGuard({} as never, {} as never));
    expect(result).toBe(true);
  });
});
