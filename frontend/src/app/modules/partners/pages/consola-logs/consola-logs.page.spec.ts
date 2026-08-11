import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import type { TestRequest } from '@angular/common/http/testing';

import { ConsolaLogsPage } from './consola-logs.page';
import type { LogLlamada } from '../../services/models/monitoreo.types';

const PARTNERS = [
  {
    idpartner: 12,
    idcliente: 3,
    nombrepartner: 'Integradora Andina',
    planapi: 'Profesional',
    limitellamadasmes: 10000,
    limitellamadasminuto: 120,
    activo: true,
    estado: 'Producción activa',
  },
];

function log(id: number, codigo: number, fecha = 1_750_000_000_000): LogLlamada {
  return {
    idlogllamadaapi: id,
    idpartner: 12,
    endpoint: '/api/v1/datos/accidentes',
    metodohttp: 'GET',
    codigohttp: codigo,
    latenciams: 90,
    iporigen: 3232235777,
    fechallamada: fecha,
  };
}

describe('ConsolaLogsPage', () => {
  let fixture: ComponentFixture<ConsolaLogsPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConsolaLogsPage],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ConsolaLogsPage);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http
      .expectOne((r) => r.url === '/api/v1/partners')
      .flush({ data: PARTNERS, meta: { pagination: null } });
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  /** Responde la petición de logs pendiente y devuelve la request, para inspeccionarla. */
  function responder(logs: LogLlamada[], next: number | null = null): TestRequest {
    const req = http.expectOne((r) => r.url === '/api/v1/logs-api');
    req.flush({
      data: logs,
      meta: {
        pagination: {
          next_cursor: next,
          // El cursor es COMPUESTO: sin la fecha, la página siguiente repite
          // filas cuando el id no desciende con el tiempo.
          next_cursor_fecha: next === null ? null : 1_750_000_000_000,
          limit: 50,
        },
      },
    });
    fixture.detectChanges();
    return req;
  }

  function elegirPartner(logs: LogLlamada[], next: number | null = null): TestRequest {
    fixture.componentInstance.cambiarPartner(12);
    return responder(logs, next);
  }

  describe('elección de partner', () => {
    it('sin partner elegido NO llama al endpoint y pide elegir uno', () => {
      // El backend devuelve 400 sin idpartner: la UI se adelanta.
      // Assert
      http.expectNone((r) => r.url === '/api/v1/logs-api');
      expect(
        fixture.nativeElement.querySelector('app-list-empty-state').textContent,
      ).toContain('Elige un partner');
    });

    it('el selector ofrece los partners por NOMBRE, no por id', () => {
      expect(
        fixture.nativeElement.querySelector('[data-testid="select-partner"]').textContent,
      ).toContain('Integradora Andina');
    });

    it('al elegir partner carga sus registros', () => {
      // Act
      elegirPartner([log(1, 200)]);

      // Assert
      expect(fixture.nativeElement.querySelectorAll('[data-testid="fila-log"]').length).toBe(1);
    });
  });

  describe('🎯 cada filtro es una consulta a la base', () => {
    it('«solo errores» dispara una consulta con su parámetro', () => {
      // Arrange
      elegirPartner([log(1, 200)]);

      // Act
      fixture.componentInstance.cambiarSoloErrores(true);

      // Assert
      const req = responder([log(2, 500)]);
      expect(req.request.params.get('solo_errores')).toBe('true');
    });

    it('el código HTTP dispara una consulta con `codigohttp`, no filtra en memoria', () => {
      // Arrange
      elegirPartner([log(1, 200), log(2, 429)]);

      // Act
      fixture.componentInstance.cambiarCodigo(429);

      // Assert — hay petición nueva y el filtro viaja en ella
      const req = responder([log(2, 429)]);
      expect(req.request.params.get('codigohttp')).toBe('429');
      expect(fixture.componentInstance.logs().length).toBe(1);
    });

    it('la fecha «desde» viaja como epoch ms', () => {
      // Arrange
      elegirPartner([log(1, 200)]);

      // Act
      fixture.componentInstance.cambiarDesde('2025-06-15');

      // Assert
      const req = responder([]);
      expect(req.request.params.get('desde')).toBe(String(new Date('2025-06-15').getTime()));
    });

    it('la fecha «hasta» incluye el día elegido', () => {
      // El backend usa `<` para `hasta`; sin sumar el día, elegir el 15 dejaría
      // fuera todo lo ocurrido ese mismo día.
      // Arrange
      elegirPartner([log(1, 200)]);

      // Act
      fixture.componentInstance.cambiarHasta('2025-06-15');

      // Assert
      const req = responder([]);
      const esperado = new Date('2025-06-15').getTime() + 86_400_000;
      expect(req.request.params.get('hasta')).toBe(String(esperado));
    });

    it('limpiar el filtro de código vuelve a consultar sin él', () => {
      // Arrange
      elegirPartner([log(1, 200)]);
      fixture.componentInstance.cambiarCodigo(429);
      responder([log(2, 429)]);

      // Act
      fixture.componentInstance.cambiarCodigo('');

      // Assert
      const req = responder([log(1, 200), log(2, 429)]);
      expect(req.request.params.has('codigohttp')).toBeFalse();
    });

    it('la UI declara que los filtros alcanzan TODO el historial', () => {
      // Ya no se filtra sobre una ventana: decir lo contrario sería mentir.
      // Assert
      const alcance = fixture.nativeElement.querySelector('[data-testid="alcance-filtros"]');
      expect(alcance.textContent).toContain('todo el historial');
      expect(alcance.textContent).not.toContain('cargados');
    });
  });

  describe('🎯 paginación real por cursor', () => {
    it('muestra «Cargar más» solo si el servidor dio cursor', () => {
      // Act — sin cursor
      elegirPartner([log(1, 200)], null);

      // Assert
      expect(fixture.nativeElement.querySelector('[data-testid="btn-cargar-mas"]')).toBeNull();
    });

    it('con cursor ofrece «Cargar más»', () => {
      // Act
      elegirPartner([log(5, 200)], 5);

      // Assert
      expect(fixture.nativeElement.querySelector('[data-testid="btn-cargar-mas"]')).toBeTruthy();
    });

    it('«Cargar más» envía el cursor y AÑADE las filas, no las reemplaza', () => {
      // Arrange
      elegirPartner([log(5, 200), log(4, 200)], 4);

      // Act
      fixture.componentInstance.cargarMas();

      // Assert
      const req = responder([log(3, 200), log(2, 200)], 2);
      expect(req.request.params.get('cursor')).toBe('4');
      expect(req.request.params.get('cursor_fecha')).toBe('1750000000000');
      expect(fixture.componentInstance.logs().length).toBe(4);
    });

    it('la siguiente página conserva los filtros activos', () => {
      // Arrange
      elegirPartner([log(9, 429)], 9);
      fixture.componentInstance.cambiarCodigo(429);
      responder([log(9, 429)], 9);

      // Act
      fixture.componentInstance.cargarMas();

      // Assert — sin esto, «Cargar más» traería filas que el filtro escondería
      const req = responder([log(8, 429)], null);
      expect(req.request.params.get('codigohttp')).toBe('429');
      expect(req.request.params.get('cursor')).toBe('9');
      expect(req.request.params.get('cursor_fecha')).toBeTruthy();
    });

    it('cambiar un filtro REINICIA la paginación', () => {
      // Arrange — dos páginas acumuladas
      elegirPartner([log(9, 200)], 9);
      fixture.componentInstance.cargarMas();
      responder([log(8, 200)], 8);
      expect(fixture.componentInstance.logs().length).toBe(2);

      // Act
      fixture.componentInstance.cambiarSoloErrores(true);

      // Assert — la nueva consulta va sin cursor y reemplaza lo anterior
      const req = responder([log(7, 500)], null);
      expect(req.request.params.has('cursor')).toBeFalse();
      expect(req.request.params.has('cursor_fecha')).toBeFalse();
      expect(fixture.componentInstance.logs().length).toBe(1);
    });
  });

  describe('refresco', () => {
    it('el auto-refresco está APAGADO al entrar', () => {
      expect(fixture.componentInstance.autoRefresco()).toBeFalse();
      expect(
        fixture.nativeElement.querySelector('[data-testid="chk-auto-refresco"]').checked,
      ).toBeFalse();
    });

    it('muestra hasta cuándo hay datos y advierte del retraso de ingesta', () => {
      // Act
      elegirPartner([log(1, 200)]);

      // Assert
      expect(
        fixture.nativeElement.querySelector('[data-testid="sincronizacion"]').textContent,
      ).toContain('Datos hasta');
      expect(
        fixture.nativeElement.querySelector('[data-testid="leyenda-ingesta"]').textContent,
      ).toContain('ingesta');
    });
  });

  describe('tabla', () => {
    it('la columna de acción tiene SOLO el ojo — append-only', () => {
      // Act
      elegirPartner([log(1, 200)]);

      // Assert
      const html = fixture.nativeElement.innerHTML;
      expect(fixture.nativeElement.querySelector('[data-testid="btn-ver"]')).toBeTruthy();
      expect(html).not.toContain('Editar');
      expect(html).not.toContain('aria-label="Eliminar"');
    });

    it('el 429 se distingue del 403 y del 500', () => {
      // Act
      elegirPartner([log(1, 429), log(2, 403), log(3, 500)]);

      // Assert
      expect(
        fixture.nativeElement.querySelector('[data-testid="badge-429"]').textContent,
      ).toContain('Límite de ritmo');
      expect(
        fixture.nativeElement.querySelector('[data-testid="badge-500"]').textContent,
      ).toContain('Error de plataforma');
    });

    it('la IP se muestra en notación con puntos, no como entero', () => {
      // Act
      elegirPartner([log(1, 200)]);

      // Assert
      expect(fixture.nativeElement.innerHTML).toContain('192.168.1.1');
      expect(fixture.nativeElement.innerHTML).not.toContain('3232235777');
    });
  });

  describe('estados no felices', () => {
    it('un 403 se explica sin ofrecer reintentar de forma engañosa', () => {
      // Act
      fixture.componentInstance.cambiarPartner(12);
      http
        .expectOne((r) => r.url === '/api/v1/logs-api')
        .flush(null, { status: 403, statusText: 'Forbidden' });
      fixture.detectChanges();

      // Assert
      expect(
        fixture.nativeElement.querySelector('app-list-error-state').textContent,
      ).toContain('No tienes acceso');
    });

    it('un 400 apunta a los filtros, que es donde estará el problema', () => {
      // Act
      fixture.componentInstance.cambiarPartner(12);
      http
        .expectOne((r) => r.url === '/api/v1/logs-api')
        .flush(null, { status: 400, statusText: 'Bad Request' });
      fixture.detectChanges();

      // Assert
      expect(
        fixture.nativeElement.querySelector('app-list-error-state').textContent,
      ).toContain('Revisa los filtros');
    });

    it('un resultado vacío menciona los filtros aplicados', () => {
      // Act
      elegirPartner([]);

      // Assert
      expect(
        fixture.nativeElement.querySelector('app-list-empty-state').textContent,
      ).toContain('con los filtros aplicados');
    });
  });
});
