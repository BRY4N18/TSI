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

  it('guardarConductorPendiente_when_offline_does_not_persist_pii_plaintext', async () => {
    // Arrange
    const idaccidente = 'ACC-PII-1';
    const identificacion = '0911223344';
    const nombres = 'María';
    const apellidos = 'López';

    // Act
    await service.guardarConductorPendiente(
      idaccidente,
      { identificacion, nombres, apellidos },
      1,
      { tipovehiculo: 'Auto' },
      Date.now(),
      'cond-1',
    );
    const raw = await service.listarConductoresCifradosRaw(idaccidente);
    const serialized = JSON.stringify(raw);

    // Assert — falla si PII queda en claro en IndexedDB
    expect(raw.length).toBe(1);
    expect(raw[0].ciphertext).toBeTruthy();
    expect(serialized).not.toContain(identificacion);
    expect(serialized).not.toContain(nombres);
    expect(serialized).not.toContain(apellidos);
  });

  it('guardarImplicadoPendiente_when_offline_stores_ontology_fields_without_crypto', async () => {
    const idaccidente = 'ACC-IMP-1';
    await service.guardarImplicadoPendiente(
      idaccidente,
      { tipoimplicado: 'Peaton', estadoimplicado: 'Lesionado', edad: 22 },
      Date.now(),
      'imp-1',
    );
    const pendientes = await service.listarEnriquecimientoPendiente(idaccidente);
    expect(pendientes.implicados.length).toBe(1);
    expect(pendientes.implicados[0].payload.tipoimplicado).toBe('Peaton');
    expect(pendientes.implicados[0].payload.estadoimplicado).toBe('Lesionado');
    expect(JSON.stringify(pendientes.implicados[0])).not.toContain('identificacion');
  });
});
