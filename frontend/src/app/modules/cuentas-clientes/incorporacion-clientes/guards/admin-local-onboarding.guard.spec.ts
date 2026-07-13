import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, isObservable } from 'rxjs';

import { AuthApiService } from '../../auth/services/auth-api.service';
import { IncorporacionClienteApiService } from '../services/incorporacion-cliente-api.service';
import { adminLocalOnboardingGuard } from './admin-local-onboarding.guard';

describe('AdminLocalOnboardingGuard', () => {
  it('allows_when_administrador', (done) => {
    TestBed.configureTestingModule({
      providers: [
        { provide: Router, useValue: { createUrlTree: () => '/denied' } },
        {
          provide: AuthApiService,
          useValue: {
            getProfile: () => ({ idusuario: 1, roles: ['Administrador'], gmail: 'a@t.com' }),
          },
        },
        { provide: IncorporacionClienteApiService, useValue: { getOnboardingProgreso: () => of() } },
      ],
    });

    const route = { paramMap: { get: () => '1' } } as never;
    const result = TestBed.runInInjectionContext(() =>
      adminLocalOnboardingGuard(route, {} as never),
    );

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

  it('allows_when_cliente_with_onboarding_access', (done) => {
    TestBed.configureTestingModule({
      providers: [
        { provide: Router, useValue: { createUrlTree: () => '/denied' } },
        {
          provide: AuthApiService,
          useValue: {
            getProfile: () => ({ idusuario: 3, roles: ['Cliente'], gmail: 'c@t.com' }),
          },
        },
        {
          provide: IncorporacionClienteApiService,
          useValue: {
            getOnboardingProgreso: () =>
              of({
                data: {
                  idcliente: 1,
                  estado_onboarding: 'Pendiente',
                  etapas_completadas: [],
                  etapa_actual: 'cambio_password',
                },
                meta: { pagination: null },
              }),
          },
        },
      ],
    });

    const route = { paramMap: { get: () => '1' } } as never;
    const result = TestBed.runInInjectionContext(() =>
      adminLocalOnboardingGuard(route, {} as never),
    );

    if (isObservable(result)) {
      result.subscribe((allowed) => {
        expect(allowed).toBeTrue();
        done();
      });
    } else {
      fail('Expected observable guard result');
      done();
    }
  });
});
