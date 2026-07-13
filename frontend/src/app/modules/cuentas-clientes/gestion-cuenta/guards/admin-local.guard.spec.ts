import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, isObservable } from 'rxjs';

import { AuthApiService } from '../../auth/services/auth-api.service';
import { CuentaClienteApiService } from '../services/cuenta-cliente-api.service';
import { adminLocalGuard } from './admin-local.guard';

describe('AdminLocalGuard', () => {
  it('allows_when_user_is_admin_local', (done) => {
    TestBed.configureTestingModule({
      providers: [
        { provide: Router, useValue: { createUrlTree: () => '/denied' } },
        {
          provide: AuthApiService,
          useValue: { getProfile: () => ({ idusuario: 3, roles: ['Cliente'], gmail: 'c@t.com' }) },
        },
        {
          provide: CuentaClienteApiService,
          useValue: {
            getPerfil: () =>
              of({
                data: { admin_local_id: 3, idcliente: 1, estado: 'Activo' },
                meta: { pagination: null },
              }),
          },
        },
      ],
    });

    const route = { paramMap: { get: () => '1' } } as never;
    const result = TestBed.runInInjectionContext(() => adminLocalGuard(route, {} as never));

    if (typeof result === 'boolean') {
      expect(result).toBeTrue();
      done();
    } else if (isObservable(result)) {
      result.subscribe((allowed) => {
        expect(allowed).toBeTrue();
        done();
      });
    } else {
      fail('Unexpected guard result type');
      done();
    }
  });
});
