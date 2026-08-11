import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MiConsumoPage } from './mi-consumo.page';
import type { ConsumoPartner, LogLlamada } from '../../services/models/monitoreo.types';

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

function consumo(parcial: Partial<ConsumoPartner> = {}): ConsumoPartner {
  return {
    idpartner: 12,
    entorno: 'Producción',
    periodo: { desde: 1, hasta: 2 },
    llamadas: 8400,
    errores: 12,
    latencia_media_ms: 92.5,
    cupo_mensual: 10000,
    porcentaje_consumido: 84,
    llamadas_excedentes: 0,
    excedente_estimado: 0,
    datos_hasta: 1_750_000_000_000,
    ...parcial,
  };
}

describe('MiConsumoPage', () => {
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

  /** Resuelve el flujo completo: /me → métricas → logs de errores. */
  function cargar(
    datos: Partial<ConsumoPartner> = {},
    errores: LogLlamada[] = [],
    partner = PARTNER,
  ): void {
    fixture.detectChanges();
    http
      .expectOne('/api/v1/partners/me')
      .flush({ data: partner, meta: { pagination: null } });
    http
      .expectOne((r) => r.url === `/api/v1/partners/${partner.idpartner}/metricas`)
      .flush({ data: consumo(datos), meta: { pagination: null } });
    http
      .expectOne((r) => r.url === '/api/v1/logs-api')
      .flush({ data: errores, meta: { pagination: null } });
    fixture.detectChanges();
  }

  function texto(testid: string): string {
    const el = fixture.nativeElement.querySelector(`[data-testid="${testid}"]`);
    return el ? (el.textContent ?? '').trim() : '';
  }

  describe('camino feliz', () => {
    it('resuelve /partners/me ANTES de pedir métricas', () => {
      // Act — si pidiera métricas primero, no sabría de qué partner
      fixture.detectChanges();

      // Assert
      http.expectOne('/api/v1/partners/me').flush({
        data: PARTNER,
        meta: { pagination: null },
      });
      http
        .expectOne((r) => r.url === '/api/v1/partners/12/metricas')
        .flush({ data: consumo(), meta: { pagination: null } });
      http.expectOne((r) => r.url === '/api/v1/logs-api').flush({
        data: [],
        meta: { pagination: null },
      });
    });

    it('pinta llamadas, errores y latencia', () => {
      // Act
      cargar();

      // Assert
      expect(texto('kpi-llamadas')).toContain('8');
      expect(texto('kpi-errores')).toContain('12');
      expect(texto('kpi-latencia')).toContain('92.5');
    });

    it('declara el entorno con texto, no solo con color', () => {
      // Act
      cargar();

      // Assert — RN-APM-001
      expect(texto('badge-entorno')).toBe('Producción');
    });

    it('muestra hasta cuándo hay datos y no promete tiempo real', () => {
      // Act
      cargar();

      // Assert
      expect(texto('datos-hasta')).toContain('Datos disponibles hasta');
      expect(texto('datos-hasta')).toContain('puede no aparecer');
    });
  });

  describe('centinelas en pantalla', () => {
    it('sin cupo configurado muestra «No aplica», nunca 0 %', () => {
      // Act
      cargar({ porcentaje_consumido: null, cupo_mensual: -1 });

      // Assert
      expect(texto('porcentaje-cupo')).toContain('No aplica');
      expect(texto('porcentaje-cupo')).not.toContain('0 %');
    });

    it('sin tarifa configurada muestra «No aplica», nunca 0,00', () => {
      // Act
      cargar({ llamadas_excedentes: 2500, excedente_estimado: null });

      // Assert
      const importe = texto('importe-excedente');
      expect(importe).toContain('No aplica');
      expect(importe).not.toContain('0,00');
      expect(importe).not.toContain('$');
    });

    it('un excedente con tarifa sí muestra su importe', () => {
      // Act
      cargar({ llamadas_excedentes: 2500, excedente_estimado: 12.5 });

      // Assert
      expect(texto('importe-excedente')).toContain('12');
    });
  });

  describe('partner suspendido', () => {
    it('🎯 NO dice «tu servicio no se interrumpe» si el acceso está cortado', () => {
      // Las dos frases son ciertas por separado y juntas se contradicen: el
      // banner dice que el acceso está suspendido y el copy del cupo diría que
      // el servicio sigue. Se detectó mirando la pantalla real.
      // Arrange / Act
      cargar({ porcentaje_consumido: 150, llamadas_excedentes: 5000, excedente_estimado: 25 },
             [], { ...PARTNER, activo: false });

      // Assert
      const pagina = (fixture.nativeElement.textContent ?? '').toLowerCase();
      expect(pagina).toContain('suspendido');
      expect(pagina).not.toContain('no se interrumpe');
      // El encuadre de facturación se mantiene: sigue siendo un coste
      expect(texto('copy-cupo')).toContain('se factura');
    });

    it('un partner ACTIVO con exceso sí ve la frase de tranquilidad', () => {
      // Arrange / Act
      cargar({ porcentaje_consumido: 150, llamadas_excedentes: 5000, excedente_estimado: 25 });

      // Assert
      expect(texto('copy-cupo')).toContain('no se interrumpe');
    });

    it('carga sus métricas con normalidad y añade un banner', () => {
      // Arrange / Act — RN-APM-017: es lectura, y le explica su situación
      cargar({}, [], { ...PARTNER, activo: false, motivo_suspension: 'Mora' });

      // Assert
      expect(texto('banner-suspendido')).toContain('suspendido');
      expect(texto('kpi-llamadas')).toContain('8');
    });
  });

  describe('estados no felices', () => {
    it('muestra el esqueleto mientras carga', () => {
      // Act
      fixture.detectChanges();

      // Assert
      expect(fixture.nativeElement.querySelector('app-list-loading-skeleton')).toBeTruthy();
      http.expectOne('/api/v1/partners/me').flush({ data: PARTNER, meta: { pagination: null } });
      http
        .expectOne((r) => r.url === '/api/v1/partners/12/metricas')
        .flush({ data: consumo(), meta: { pagination: null } });
      http.expectOne((r) => r.url === '/api/v1/logs-api').flush({
        data: [],
        meta: { pagination: null },
      });
    });

    it('un 404 de /me explica el problema y NO ofrece reintentar', () => {
      // Arrange / Act — reintentar no lo vinculará a ningún partner
      fixture.detectChanges();
      http
        .expectOne('/api/v1/partners/me')
        .flush({ error: 'not_found', detail: '', code: 'not_found' }, { status: 404, statusText: 'Not Found' });
      fixture.detectChanges();

      // Assert
      const error = fixture.nativeElement.querySelector('app-list-error-state');
      expect(error.textContent).toContain('no está vinculado a ningún partner');
      expect(fixture.componentInstance.puedeReintentar()).toBeFalse();
    });

    it('un fallo de red sí ofrece reintentar', () => {
      // Act
      fixture.detectChanges();
      http
        .expectOne('/api/v1/partners/me')
        .flush(null, { status: 500, statusText: 'Server Error' });
      fixture.detectChanges();

      // Assert
      expect(fixture.componentInstance.puedeReintentar()).toBeTrue();
    });

    it('que fallen los logs NO impide ver el consumo', () => {
      // Arrange / Act — fail-open: el consumo es lo principal
      fixture.detectChanges();
      http.expectOne('/api/v1/partners/me').flush({ data: PARTNER, meta: { pagination: null } });
      http
        .expectOne((r) => r.url === '/api/v1/partners/12/metricas')
        .flush({ data: consumo(), meta: { pagination: null } });
      http
        .expectOne((r) => r.url === '/api/v1/logs-api')
        .flush(null, { status: 500, statusText: 'Server Error' });
      fixture.detectChanges();

      // Assert
      expect(texto('kpi-llamadas')).toContain('8');
    });
  });
});
