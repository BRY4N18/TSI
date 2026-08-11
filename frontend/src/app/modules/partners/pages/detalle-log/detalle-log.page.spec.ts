import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';

import { DetalleLogPage } from './detalle-log.page';
import type { LogLlamada } from '../../services/models/monitoreo.types';

const LOG: LogLlamada = {
  idlogllamadaapi: 7,
  idpartner: 12,
  endpoint: '/api/v1/datos/accidentes',
  metodohttp: 'GET',
  codigohttp: 429,
  latenciams: 88,
  iporigen: 3232235777,
  fechallamada: 1_750_000_000_000,
};

function configurar(idlog = '7', idpartner: string | null = '12') {
  return TestBed.configureTestingModule({
    imports: [DetalleLogPage],
    providers: [
      provideHttpClient(),
      provideHttpClientTesting(),
      provideRouter([]),
      {
        provide: ActivatedRoute,
        useValue: {
          snapshot: {
            paramMap: { get: () => idlog },
            queryParamMap: { get: () => idpartner },
          },
        },
      },
    ],
  }).compileComponents();
}

describe('DetalleLogPage', () => {
  let fixture: ComponentFixture<DetalleLogPage>;
  let http: HttpTestingController;

  afterEach(() => http?.verify());

  describe('modo Ver', () => {
    beforeEach(async () => {
      await configurar();
      fixture = TestBed.createComponent(DetalleLogPage);
      http = TestBed.inject(HttpTestingController);
      fixture.detectChanges();
      http
        .expectOne((r) => r.url === '/api/v1/logs-api')
        .flush({ data: [LOG], meta: { pagination: null } });
      fixture.detectChanges();
    });

    it('lleva el chrome del golden sample: volver + eyebrow + h1 con badge', () => {
      // Assert
      expect(
        fixture.nativeElement.querySelector('[data-testid="volver"]').textContent,
      ).toContain('Volver a los registros');
      expect(fixture.nativeElement.querySelector('[data-testid="eyebrow"]').textContent.trim()).toBe(
        'Detalles',
      );
      expect(fixture.nativeElement.querySelector('h1').textContent).toContain('/datos/accidentes');
      expect(fixture.nativeElement.querySelector('[data-testid="badge-codigo"]')).toBeTruthy();
    });

    it('🎯 usa <dl>, NUNCA <input disabled> para fingir solo lectura', () => {
      // Assert — el design-system lo prohíbe explícitamente
      expect(fixture.nativeElement.querySelector('dl')).toBeTruthy();
      expect(fixture.nativeElement.querySelector('input')).toBeNull();
    });

    it('no hay botón de guardado ni acciones de dominio', () => {
      // Un log es append-only: no hay nada que hacerle (RN-APM-015)
      // Assert
      const texto = (fixture.nativeElement.textContent ?? '').toLowerCase();
      expect(texto).not.toContain('guardar');
      expect(texto).not.toContain('editar');
      expect(texto).not.toContain('eliminar');
    });

    it('dice si la llamada cuenta como consumo facturable', () => {
      // Assert — el 429 no se atendió, así que no se factura
      expect(
        fixture.nativeElement.querySelector('[data-testid="dd-consumo"]').textContent,
      ).toContain('No cuenta como consumo facturable');
    });

    it('formatea la IP entera', () => {
      expect(fixture.nativeElement.innerHTML).toContain('192.168.1.1');
    });
  });

  describe('sin idpartner en la URL', () => {
    beforeEach(async () => {
      await configurar('7', null);
      fixture = TestBed.createComponent(DetalleLogPage);
      http = TestBed.inject(HttpTestingController);
      fixture.detectChanges();
    });

    it('explica cómo abrirlo en vez de provocar un 400', () => {
      // Assert — el endpoint exige idpartner; la UI no lo llama a ciegas
      http.expectNone((r) => r.url === '/api/v1/logs-api');
      expect(
        fixture.nativeElement.querySelector('app-list-error-state').textContent,
      ).toContain('desde la lista');
    });
  });
});
