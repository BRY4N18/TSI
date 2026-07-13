import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, isObservable } from 'rxjs';

import { AuthApiService } from '../../auth/services/auth-api.service';
import { IncorporacionClienteApiService } from '../services/incorporacion-cliente-api.service';
import { onboardingCompletadoGuard } from './onboarding-completado.guard';

describe('OnboardingCompletadoGuard', () => {
  it('redirects_when_onboarding_incompleto', (done) => {
    const urlTree = '/incorporacion-clientes/1/onboarding';
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
                  estado_onboarding: 'En progreso',
                  etapas_completadas: ['cambio_password'],
                  etapa_actual: 'perfil_corporativo',
                },
                meta: { pagination: null },
              }),
          },
        },
      ],
    });

    const route = { paramMap: { get: () => '1' } } as never;
    const result = TestBed.runInInjectionContext(() =>
      onboardingCompletadoGuard(route, {} as never),
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

  it('allows_when_onboarding_completado', (done) => {
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
      onboardingCompletadoGuard(route, {} as never),
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
