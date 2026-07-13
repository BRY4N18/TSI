import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of } from 'rxjs';

import { CuentaClienteApiService } from '../services/cuenta-cliente-api.service';
import { cuentaActivaGuard } from './cuenta-activa.guard';

describe('CuentaActivaGuard', () => {
  it('allows_when_cuenta_is_activa', (done) => {
    TestBed.configureTestingModule({
      providers: [
        { provide: Router, useValue: { createUrlTree: () => '/home' } },
        {
          provide: CuentaClienteApiService,
          useValue: {
            getPerfil: () =>
              of({
                data: { idcliente: 1, estado: 'Activo', admin_local_id: 3 },
                meta: { pagination: null },
              }),
          },
        },
      ],
    });

    const route = { paramMap: { get: () => '1' } } as never;
    const result = TestBed.runInInjectionContext(() => cuentaActivaGuard(route, {} as never));

    (result as ReturnType<typeof of>).subscribe((allowed) => {
      expect(allowed).toBeTrue();
      done();
    });
  });
});
