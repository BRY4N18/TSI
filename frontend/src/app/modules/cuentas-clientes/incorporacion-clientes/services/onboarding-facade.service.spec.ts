import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { OnboardingFacadeService } from './onboarding-facade.service';
import { IncorporacionClienteApiService } from './incorporacion-cliente-api.service';

describe('OnboardingFacadeService', () => {
  let facade: OnboardingFacadeService;
  let api: jasmine.SpyObj<IncorporacionClienteApiService>;

  beforeEach(() => {
    api = jasmine.createSpyObj('IncorporacionClienteApiService', [
      'getOnboardingProgreso',
      'completarEtapa',
    ]);

    TestBed.configureTestingModule({
      providers: [
        OnboardingFacadeService,
        { provide: IncorporacionClienteApiService, useValue: api },
      ],
    });
    facade = TestBed.inject(OnboardingFacadeService);
  });

  it('loadProgreso_when_ok_returns_data', (done) => {
    // Arrange
    const progreso = {
      idcliente: 1,
      estado_onboarding: 'En progreso' as const,
      etapas_completadas: ['cambio_password' as const],
      etapa_actual: 'perfil_corporativo' as const,
    };
    api.getOnboardingProgreso.and.returnValue(
      of({ data: progreso, meta: { pagination: null } }),
    );

    // Act
    facade.loadProgreso(1).subscribe((data) => {
      // Assert
      expect(data.etapa_actual).toBe('perfil_corporativo');
      done();
    });
  });

  it('etapaLabel_returns_human_readable', () => {
    // Arrange & Act & Assert
    expect(facade.etapaLabel('cambio_password')).toBe('Cambio de contraseña');
    expect(facade.etapaLabel(null)).toBe('Completado');
  });
});
