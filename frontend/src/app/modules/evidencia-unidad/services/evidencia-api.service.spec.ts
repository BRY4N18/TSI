/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { EvidenciaApiService } from './evidencia-api.service';
import { EvidenciaOfflineStoreService } from './evidencia-offline-store.service';

describe('EvidenciaApiService', () => {
  let service: EvidenciaApiService;
  let http: HttpTestingController;
  let offlineStore: jasmine.SpyObj<EvidenciaOfflineStoreService>;

  beforeEach(() => {
    offlineStore = jasmine.createSpyObj<EvidenciaOfflineStoreService>(
      'EvidenciaOfflineStoreService',
      ['listarPendientes', 'eliminarFoto', 'eliminarNota'],
    );
    offlineStore.listarPendientes.and.resolveTo({ fotos: [], notas: [] });

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        EvidenciaApiService,
        { provide: EvidenciaOfflineStoreService, useValue: offlineStore },
      ],
    });
    service = TestBed.inject(EvidenciaApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('listarServidor_when_ok_returns_items', () => {
    // Arrange
    const mock = {
      data: { items: [] },
      meta: { pagination: null },
    };

    // Act
    service.listarServidor('ACC-1-2026').subscribe((res) => {
      // Assert
      expect(res.data.items).toEqual([]);
    });

    const req = http.expectOne('/api/v1/accidentes/ACC-1-2026/evidencias');
    expect(req.request.method).toBe('GET');
    req.flush(mock);
  });
});
