/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { administradorSlaGuard } from './administrador-sla.guard';
import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

describe('administradorSlaGuard', () => {
  it('allows_administrador_role', () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: (r: string) => r === 'Administrador' },
        },
        { provide: Router, useValue: { createUrlTree: () => false } },
      ],
    });
    const result = TestBed.runInInjectionContext(() =>
      administradorSlaGuard({} as never, {} as never),
    );
    expect(result).toBe(true);
  });

  it('denies_soporte_role', () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: { isAuthenticated: () => true, hasRole: (r: string) => r === 'Soporte' },
        },
        { provide: Router, useValue: { createUrlTree: () => 'redirected' } },
      ],
    });
    const result = TestBed.runInInjectionContext(() =>
      administradorSlaGuard({} as never, {} as never),
    );
    expect(result as unknown).toBe('redirected');
  });
});
