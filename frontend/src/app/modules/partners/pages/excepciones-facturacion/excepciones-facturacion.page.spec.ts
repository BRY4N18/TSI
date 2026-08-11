import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ExcepcionesFacturacionPage } from './excepciones-facturacion.page';
import type { ExcepcionFacturacion } from '../../services/models/monitoreo.types';

const AGOTADA: ExcepcionFacturacion = {
  tipo: 'reintentos_agotados',
  idpartner: 12,
  nombrepartner: 'Integradora Andina',
  periodo: '2026-07',
  id_factura: 'FAC-AGOTADA',
  importe: 42.5,
  intentos: 4,
  ultimo_resultado: 'agotados: timeout del emisor',
};

const SIN_TARIFA: ExcepcionFacturacion = {
  tipo: 'no_tarificable',
  idpartner: 77,
  nombrepartner: 'Integradora Sin Tarifa',
  periodo: '2026-07',
  id_factura: null,
  importe: null,
  intentos: null,
  ultimo_resultado: '5000 llamadas excedentes sin tarifa configurada en el plan',
};

describe('ExcepcionesFacturacionPage', () => {
  let fixture: ComponentFixture<ExcepcionesFacturacionPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ExcepcionesFacturacionPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(ExcepcionesFacturacionPage);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function cargar(
    data: ExcepcionFacturacion[],
    meta = { reintentos_agotados: 0, no_tarificables: 0 },
  ): void {
    fixture.detectChanges();
    http.expectOne((r) => r.url === '/api/v1/facturacion/excepciones').flush({ data, meta });
    fixture.detectChanges();
  }

  describe('los dos tipos', () => {
    it('🎯 los distingue por badge', () => {
      // Act
      cargar([AGOTADA, SIN_TARIFA], { reintentos_agotados: 1, no_tarificables: 1 });

      // Assert
      expect(
        fixture.nativeElement.querySelector('[data-testid="badge-reintentos_agotados"]')
          .textContent,
      ).toContain('Reintentos agotados');
      expect(
        fixture.nativeElement.querySelector('[data-testid="badge-no_tarificable"]').textContent,
      ).toContain('No tarificable');
    });

    it('🎯 el no tarificable NO muestra importe, ni siquiera 0,00', () => {
      // Un 0,00 diría «se facturó nada»; la verdad es que no se pudo calcular
      // porque el plan no tiene tarifa.
      // Act
      cargar([SIN_TARIFA], { reintentos_agotados: 0, no_tarificables: 1 });

      // Assert
      const importe = fixture.nativeElement
        .querySelector('[data-testid="importe-no_tarificable"]')
        .textContent.trim();
      expect(importe).toBe('');
      expect(importe).not.toContain('0');
    });

    it('el de reintentos agotados sí muestra su importe', () => {
      // Act
      cargar([AGOTADA], { reintentos_agotados: 1, no_tarificables: 0 });

      // Assert
      expect(
        fixture.nativeElement.querySelector('[data-testid="importe-reintentos_agotados"]')
          .textContent,
      ).toContain('42');
    });

    it('cada tipo lleva su acción sugerida, y son distintas', () => {
      // Act
      cargar([AGOTADA, SIN_TARIFA], { reintentos_agotados: 1, no_tarificables: 1 });

      // Assert
      const agotada = fixture.nativeElement.querySelector(
        '[data-testid="accion-reintentos_agotados"]',
      ).textContent;
      const sinTarifa = fixture.nativeElement.querySelector(
        '[data-testid="accion-no_tarificable"]',
      ).textContent;
      expect(agotada).toContain('Emitir la factura manualmente');
      expect(sinTarifa).toContain('precio de excedente del plan');
      expect(agotada).not.toBe(sinTarifa);
    });

    it('el resumen cuenta cada tipo por separado', () => {
      // Act
      cargar([AGOTADA, SIN_TARIFA], { reintentos_agotados: 1, no_tarificables: 1 });

      // Assert
      const resumen = fixture.nativeElement.querySelector('[data-testid="resumen"]').textContent;
      expect(resumen).toContain('1 con reintentos agotados');
      expect(resumen).toContain('1 sin tarifa configurada');
    });
  });

  describe('acciones', () => {
    it('🎯 NO existe ningún botón de emitir', () => {
      // No hay endpoint de emisión manual: un botón que no hace nada sería peor
      // que decir cuál es el siguiente paso (FR-UI-135).
      // Act
      cargar([AGOTADA], { reintentos_agotados: 1, no_tarificables: 0 });

      // Assert
      const botones = Array.from(
        fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
      ).map((b) => (b.textContent ?? '').toLowerCase());
      expect(botones.some((t) => t.includes('emitir'))).toBeFalse();
      expect(botones.some((t) => t.includes('reintentar factura'))).toBeFalse();
    });
  });

  describe('estados no felices', () => {
    it('🎯 la cola vacía se redacta en POSITIVO', () => {
      // Aquí vacío es el estado deseable, no la ausencia de datos.
      // Act
      cargar([]);

      // Assert
      const vacio = fixture.nativeElement.querySelector('app-list-empty-state');
      expect(vacio.textContent).toContain('No hay excepciones de facturación pendientes');
      expect(vacio.textContent).toContain('se facturó correctamente');
    });

    it('un 403 se explica sin ofrecer reintentar de forma engañosa', () => {
      // Act
      fixture.detectChanges();
      http
        .expectOne((r) => r.url === '/api/v1/facturacion/excepciones')
        .flush(null, { status: 403, statusText: 'Forbidden' });
      fixture.detectChanges();

      // Assert
      expect(
        fixture.nativeElement.querySelector('app-list-error-state').textContent,
      ).toContain('No tienes acceso');
    });

    it('muestra el esqueleto mientras carga', () => {
      // Act
      fixture.detectChanges();

      // Assert
      expect(fixture.nativeElement.querySelector('app-list-loading-skeleton')).toBeTruthy();
      http
        .expectOne((r) => r.url === '/api/v1/facturacion/excepciones')
        .flush({ data: [], meta: { reintentos_agotados: 0, no_tarificables: 0 } });
    });
  });

  it('consulta el período elegido', () => {
    // Arrange
    cargar([]);

    // Act
    fixture.componentInstance.anio.set(2026);
    fixture.componentInstance.mes.set(3);
    fixture.componentInstance.cargar();

    // Assert
    const req = http.expectOne((r) => r.url === '/api/v1/facturacion/excepciones');
    expect(req.request.params.get('anio')).toBe('2026');
    expect(req.request.params.get('mes')).toBe('3');
    req.flush({ data: [], meta: { reintentos_agotados: 0, no_tarificables: 0 } });
  });
});
