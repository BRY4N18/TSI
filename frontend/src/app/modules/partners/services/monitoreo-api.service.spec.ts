import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

import { MonitoreoApiService } from './monitoreo-api.service';

describe('MonitoreoApiService', () => {
  let service: MonitoreoApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(MonitoreoApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  describe('metricas', () => {
    it('pide el entorno de producción por defecto', () => {
      // Act
      service.metricas(12).subscribe();

      // Assert — RN-APM-001: el consumo de pruebas nunca se mezcla
      const req = http.expectOne((r) => r.url === '/api/v1/partners/12/metricas');
      expect(req.request.params.get('entorno')).toBe('Producción');
      req.flush({ data: {}, meta: { pagination: null } });
    });
  });

  describe('logs', () => {
    it('envía idpartner y limit', () => {
      // Act
      service.logs({ idpartner: 12, limit: 50 }).subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === '/api/v1/logs-api');
      expect(req.request.params.get('idpartner')).toBe('12');
      expect(req.request.params.get('limit')).toBe('50');
      req.flush({ data: [], meta: { pagination: null } });
    });

    it('solo envía solo_errores cuando se pide', () => {
      // Act
      service.logs({ idpartner: 12 }).subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === '/api/v1/logs-api');
      expect(req.request.params.has('solo_errores')).toBeFalse();
      req.flush({ data: [], meta: { pagination: null } });
    });

    it('🎯 envía el cursor de la página siguiente', () => {
      // BE-DELTA-06: hasta 2026-08-10 el endpoint anunciaba `next_cursor` en su
      // `meta` y no lo aceptaba. Ahora se le puede devolver.
      // Act
      service.logs({ idpartner: 12, cursor: 4 }).subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === '/api/v1/logs-api');
      expect(req.request.params.get('cursor')).toBe('4');
      req.flush({ data: [], meta: { pagination: null } });
    });

    it('🎯 envía código y rango temporal al SERVIDOR, no filtra en memoria', () => {
      // Act
      service
        .logs({ idpartner: 12, codigohttp: 429, desdeMs: 1000, hastaMs: 2000 })
        .subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === '/api/v1/logs-api');
      expect(req.request.params.get('codigohttp')).toBe('429');
      expect(req.request.params.get('desde')).toBe('1000');
      expect(req.request.params.get('hasta')).toBe('2000');
      req.flush({ data: [], meta: { pagination: null } });
    });

    it('un filtro sin valor no viaja como parámetro vacío', () => {
      // Act
      service.logs({ idpartner: 12, codigohttp: null, desdeMs: null }).subscribe();

      // Assert — un `codigohttp=` vacío daría 400 en el backend
      const req = http.expectOne((r) => r.url === '/api/v1/logs-api');
      expect(req.request.params.has('codigohttp')).toBeFalse();
      expect(req.request.params.has('desde')).toBeFalse();
      req.flush({ data: [], meta: { pagination: null } });
    });
  });

  describe('reporteMensual', () => {
    it('envía idpartner, anio y mes', () => {
      // Act
      service.reporteMensual(12, 2026, 7).subscribe();

      // Assert
      const req = http.expectOne((r) => r.url === '/api/v1/reportes-consumo');
      expect(req.request.params.get('anio')).toBe('2026');
      expect(req.request.params.get('mes')).toBe('7');
      req.flush({ data: {}, meta: { pagination: null } });
    });

    it('propaga el 403 de propiedad para que la página lo distinga del 5xx', () => {
      // Arrange
      let capturado: number | undefined;

      // Act
      service.reporteMensual(99, 2026, 7).subscribe({
        error: (e: { status: number }) => (capturado = e.status),
      });
      http
        .expectOne((r) => r.url === '/api/v1/reportes-consumo')
        .flush(
          { error: 'forbidden', detail: '', code: 'propiedad_partner' },
          { status: 403, statusText: 'Forbidden' },
        );

      // Assert — un 403 no ofrece «Reintentar»; un 5xx sí
      expect(capturado).toBe(403);
    });
  });
});
