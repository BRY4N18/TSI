import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MiConsumoPage } from './mi-consumo.page';
import type { ConsumoPartner, LogLlamada } from '../../services/models/monitoreo.types';

/**
 * Autodiagnóstico del partner (RN-APM-009, US-FE-2).
 *
 * Los errores de su integración se registran con su código **para que pueda
 * corregirlos sin escalar a un Administrador**. La UI los presenta como
 * información útil, no como una alarma de plataforma: son suyos, no nuestros.
 */

const PARTNER = {
  idpartner: 12,
  idcliente: 3,
  nombrepartner: 'Integradora Andina',
  planapi: 'Profesional',
  limitellamadasmes: 10000,
  limitellamadasminuto: 120,
  activo: true,
  estado: 'Producción activa',
  contacto_tecnico_nombre: 'Ana',
  contacto_tecnico_gmail: 'ana@demo.com',
  fecha_suspension: '',
  motivo_suspension: '',
  credenciales: [],
  historial: [],
};

const CONSUMO: ConsumoPartner = {
  idpartner: 12,
  entorno: 'Producción',
  periodo: { desde: 1, hasta: 2 },
  llamadas: 500,
  errores: 3,
  latencia_media_ms: 90,
  cupo_mensual: 10000,
  porcentaje_consumido: 5,
  llamadas_excedentes: 0,
  excedente_estimado: 0,
  datos_hasta: 1_750_000_000_000,
};

function log(idlogllamadaapi: number, codigohttp: number): LogLlamada {
  return {
    idlogllamadaapi,
    idpartner: 12,
    endpoint: '/api/v1/datos/accidentes',
    metodohttp: 'GET',
    codigohttp,
    latenciams: 95,
    iporigen: 3232235777,
    fechallamada: 1_750_000_000_000,
  };
}

describe('MiConsumoPage — errores del partner', () => {
  let fixture: ComponentFixture<MiConsumoPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MiConsumoPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(MiConsumoPage);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function cargar(errores: LogLlamada[]): void {
    fixture.detectChanges();
    http.expectOne('/api/v1/partners/me').flush({ data: PARTNER, meta: { pagination: null } });
    http
      .expectOne((r) => r.url === '/api/v1/partners/12/metricas')
      .flush({ data: CONSUMO, meta: { pagination: null } });
    http
      .expectOne((r) => r.url === '/api/v1/logs-api')
      .flush({ data: errores, meta: { pagination: null } });
    fixture.detectChanges();
  }

  function html(): string {
    return fixture.nativeElement.querySelector('[data-testid="bloque-errores"]').innerHTML;
  }

  it('pide solo los errores al servidor', () => {
    // Act
    fixture.detectChanges();
    http.expectOne('/api/v1/partners/me').flush({ data: PARTNER, meta: { pagination: null } });
    http
      .expectOne((r) => r.url === '/api/v1/partners/12/metricas')
      .flush({ data: CONSUMO, meta: { pagination: null } });

    // Assert
    const req = http.expectOne((r) => r.url === '/api/v1/logs-api');
    expect(req.request.params.get('solo_errores')).toBe('true');
    req.flush({ data: [], meta: { pagination: null } });
  });

  it('muestra endpoint, método y código de cada error', () => {
    // Act
    cargar([log(1, 403)]);

    // Assert
    const fila = fixture.nativeElement.querySelector('[data-testid="fila-error"]');
    expect(fila.textContent).toContain('GET');
    expect(fila.textContent).toContain('/api/v1/datos/accidentes');
    expect(fila.textContent).toContain('403');
  });

  it('🎯 el 429 se presenta como «Límite de ritmo», no como error del cliente', () => {
    // Arrange / Act — agruparlo con los 4xx haría que el partner revisara un
    // cliente que está bien: no es una petición mal formada, es ritmo regulado
    cargar([log(1, 429)]);

    // Assert
    const badge = fixture.nativeElement.querySelector('[data-testid="badge-429"]');
    expect(badge.textContent).toContain('Límite de ritmo');
    expect(badge.textContent).not.toContain('Revisar la petición');
  });

  it('🎯 el 429 avisa de que no cuenta como consumo facturable', () => {
    // Act
    cargar([log(1, 429)]);

    // Assert — § 15 D2: una petición rechazada no se atendió, no se factura
    const nota = fixture.nativeElement.querySelector('[data-testid="nota-no-facturable"]');
    expect(nota).toBeTruthy();
    expect(nota.textContent).toContain('No cuenta como consumo facturable');
  });

  it('un 403 sí es del cliente y no lleva esa nota', () => {
    // Act
    cargar([log(1, 403)]);

    // Assert
    expect(fixture.nativeElement.querySelector('[data-testid="nota-no-facturable"]')).toBeNull();
  });

  it('distingue los tres casos a la vez', () => {
    // Act
    cargar([log(1, 403), log(2, 429), log(3, 500)]);

    // Assert — tres tonos distintos: cliente, ritmo y plataforma
    const contenido = html();
    expect(contenido).toContain('alert-warning');
    expect(contenido).toContain('alert-info');
    expect(contenido).toContain('alert-critical');
  });

  it('el encabezado dice «Errores», no «Incidencias»', () => {
    // Act
    cargar([]);

    // Assert — son autodiagnóstico del partner, no incidencias de plataforma
    const bloque = fixture.nativeElement.querySelector('[data-testid="bloque-errores"]');
    expect(bloque.textContent).toContain('Errores de tu integración');
    expect(bloque.textContent.toLowerCase()).not.toContain('incidencia');
  });

  it('sin errores, el vacío se redacta en positivo', () => {
    // Act
    cargar([]);

    // Assert — es una buena noticia, no un fallo de carga
    const vacio = fixture.nativeElement.querySelector('app-list-empty-state');
    expect(vacio.textContent).toContain('respondiendo correctamente');
  });
});
