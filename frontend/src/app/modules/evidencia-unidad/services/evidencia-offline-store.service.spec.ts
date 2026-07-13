/** @marker unit */
import { TestBed } from '@angular/core/testing';

import { EvidenciaOfflineStoreService } from './evidencia-offline-store.service';

describe('EvidenciaOfflineStoreService', () => {
  let service: EvidenciaOfflineStoreService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [EvidenciaOfflineStoreService],
    });
    service = TestBed.inject(EvidenciaOfflineStoreService);
  });

  it('guardarNotaPendiente_when_ok_returns_record', async () => {
    // Arrange
    const idaccidente = 'ACC-1-2026';

    // Act
    const record = await service.guardarNotaPendiente(
      idaccidente,
      'Nota offline',
      'Observación general',
      Date.now(),
      'local-1',
    );

    // Assert
    expect(record.local_id).toBe('local-1');
    const pendientes = await service.listarPendientes(idaccidente);
    expect(pendientes.notas.length).toBe(1);
  });
});
