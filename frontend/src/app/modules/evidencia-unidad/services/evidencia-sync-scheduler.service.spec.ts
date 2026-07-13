/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { EvidenciaApiService } from './evidencia-api.service';
import { EvidenciaSyncSchedulerService } from './evidencia-sync-scheduler.service';

describe('EvidenciaSyncSchedulerService', () => {
  let service: EvidenciaSyncSchedulerService;
  let evidenciaApi: jasmine.SpyObj<EvidenciaApiService>;

  beforeEach(() => {
    evidenciaApi = jasmine.createSpyObj<EvidenciaApiService>('EvidenciaApiService', [
      'sincronizarPendientes',
    ]);
    evidenciaApi.sincronizarPendientes.and.returnValue(
      of({
        data: { sincronizados: 0, pendientes: 0, resultados: [] },
        meta: { pagination: null },
      }),
    );

    TestBed.configureTestingModule({
      providers: [
        EvidenciaSyncSchedulerService,
        { provide: EvidenciaApiService, useValue: evidenciaApi },
      ],
    });
    service = TestBed.inject(EvidenciaSyncSchedulerService);
  });

  it('registrarCaso_when_online_triggers_sync', () => {
    // Arrange
    spyOnProperty(navigator, 'onLine', 'get').and.returnValue(true);

    // Act
    service.registrarCaso('ACC-1-2026');

    // Assert
    expect(evidenciaApi.sincronizarPendientes).toHaveBeenCalledWith('ACC-1-2026');
  });
});
