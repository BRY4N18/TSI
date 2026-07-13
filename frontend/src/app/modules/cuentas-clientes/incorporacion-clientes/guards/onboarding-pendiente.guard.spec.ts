import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, isObservable } from 'rxjs';

import { AuthApiService } from '../../auth/services/auth-api.service';
import { IncorporacionClienteApiService } from '../services/incorporacion-cliente-api.service';
import { onboardingPendienteGuard } from './onboarding-pendiente.guard';

describe('OnboardingPendienteGuard', () => {
  it('redirects_when_onboarding_completado', (done) => {
    const urlTree = '/gestion-cuenta/1/perfil';
    TestBed.configureTestingModule({
      providers: [
        { provide: Router, useValue: { createUrlTree: () => urlTree } },
        {
          provide: AuthApiService,
          useValue: { getProfile: () => ({ idusuario: 3, roles: ['Cliente'], gmail: 'c@t.com' }) },
        },
        {
          provide: IncorporacionClienteApiService,
          useValue: {
            getOnboardingProgreso: () =>
              of({
                data: {
                  idcliente: 1,
                  estado_onboarding: 'Completado',
                  etapas_completadas: ['cambio_password', 'perfil_corporativo', 'preferencias'],
                  etapa_actual: null,
                },
                meta: { pagination: null },
              }),
          },
        },
      ],
    });

    const route = { paramMap: { get: () => '1' } } as never;
    const result = TestBed.runInInjectionContext(() =>
      onboardingPendienteGuard(route, {} as never),
    );

    if (isObservable(result)) {
      result.subscribe((allowed) => {
        expect(allowed as unknown).toEqual(urlTree);
        done();
      });
    } else {
      fail('Expected observable guard result');
      done();
    }
  });

  it('allows_when_onboarding_pendiente', (done) => {
    TestBed.configureTestingModule({
      providers: [
        { provide: Router, useValue: { createUrlTree: () => '/denied' } },
        {
          provide: AuthApiService,
          useValue: { getProfile: () => ({ idusuario: 3, roles: ['Cliente'], gmail: 'c@t.com' }) },
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
      onboardingPendienteGuard(route, {} as never),
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
