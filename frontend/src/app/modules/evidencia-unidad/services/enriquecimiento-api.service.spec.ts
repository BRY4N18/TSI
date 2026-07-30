/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { EnriquecimientoApiService } from './enriquecimiento-api.service';
import { EvidenciaOfflineStoreService } from './evidencia-offline-store.service';

describe('EnriquecimientoApiService', () => {
  let service: EnriquecimientoApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [EnriquecimientoApiService, EvidenciaOfflineStoreService],
    });
    service = TestBed.inject(EnriquecimientoApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('consultar_when_ok_returns_data', () => {
    // Arrange
    const mock = {
      data: {
        idaccidente: 'ACC-1',
        clima: null,
        elementos_fisicos: [],
        conductores: [],
        implicados: [],
      },
      meta: { pagination: null },
    };

    // Act
    service.consultar('ACC-1').subscribe((res) => {
      // Assert
      expect(res.data.idaccidente).toBe('ACC-1');
    });

    const req = http.expectOne('/api/v1/accidentes/ACC-1/enriquecimiento');
    expect(req.request.method).toBe('GET');
    req.flush(mock);
  });

  it('catalogoPeriodos_when_ok_returns_items', () => {
    // Arrange
    const mock = { data: { items: [{ idperiododia: 1, periododia: 'Mañana' }] }, meta: { pagination: null } };

    // Act
    service.catalogoPeriodos().subscribe((res) => {
      // Assert
      expect(res.data.items.length).toBe(1);
    });

    const req = http.expectOne('/api/v1/catalogos/periodos-dias');
    expect(req.request.method).toBe('GET');
    req.flush(mock);
  });
});
