/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { directorTecnologicoGuard } from './director-tecnologico.guard';
import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

describe('directorTecnologicoGuard', () => {
  it('allows_director_role', () => {
    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthApiService,
          useValue: {
            isAuthenticated: () => true,
            hasRole: (r: string) => r === 'DirectorTecnologico',
          },
        },
        { provide: Router, useValue: { createUrlTree: () => false } },
      ],
    });
    const result = TestBed.runInInjectionContext(() =>
      directorTecnologicoGuard({} as never, {} as never),
    );
    expect(result).toBe(true);
  });
});
