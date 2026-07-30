import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';
import { directorEstrategiaBillingGuard } from './director-estrategia-billing.guard';

describe('directorEstrategiaBillingGuard', () => {
  it('allows DirectorEstrategia when authenticated', () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: {
            isAuthenticated: () => true,
            hasRole: (r: string) => r === 'DirectorEstrategia',
          },
        },
        { provide: Router, useValue: { createUrlTree: (c: unknown) => c } },
      ],
    });
    expect(TestBed.runInInjectionContext(() => directorEstrategiaBillingGuard({} as never, {} as never))).toBe(
      true,
    );
  });

  it('denies Administrador', () => {
    const router = { createUrlTree: jasmine.createSpy('createUrlTree') };
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: {
            isAuthenticated: () => true,
            hasRole: (r: string) => r === 'Administrador',
          },
        },
        { provide: Router, useValue: router },
      ],
    });
    TestBed.runInInjectionContext(() => directorEstrategiaBillingGuard({} as never, {} as never));
    expect(router.createUrlTree).toHaveBeenCalledWith(['/cuentas-clientes/auth/access-denied']);
  });
});
