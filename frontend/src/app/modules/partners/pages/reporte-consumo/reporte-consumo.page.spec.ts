import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { ReporteConsumoPage } from './reporte-consumo.page';
import type { ReporteMensual } from '../../services/models/monitoreo.types';

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

function reporte(llamadas: number, periodo = '2026-07'): ReporteMensual {
  return {
    idpartner: 12,
    entorno: 'Producción',
    periodo,
    llamadas,
    errores: Math.floor(llamadas / 100),
    latencia_media_ms: 91,
  };
}

describe('ReporteConsumoPage', () => {
  let fixture: ComponentFixture<ReporteConsumoPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReporteConsumoPage],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ReporteConsumoPage);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http
      .expectOne((r) => r.url === '/api/v1/partners')
      .flush({ data: PARTNERS, meta: { pagination: null } });
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  function consultar(datos: ReporteMensual): void {
    fixture.componentInstance.idpartner.set(12);
    fixture.componentInstance.anio.set(2026);
    fixture.componentInstance.mes.set(7);
    fixture.componentInstance.consultar();
    http
      .expectOne((r) => r.url === '/api/v1/reportes-consumo')
      .flush({ data: datos, meta: { pagination: null } });
    fixture.detectChanges();
  }

  function texto(testid: string): string {
    const el = fixture.nativeElement.querySelector(`[data-testid="${testid}"]`);
    return el ? (el.textContent ?? '').trim() : '';
  }

  it('declara que el reporte es solo de producción', () => {
    // Assert — RN-APM-001
    expect(texto('leyenda-entorno')).toContain('producción');
  });

  it('muestra llamadas, errores y latencia del período', () => {
    // Act
    consultar(reporte(12000));

    // Assert
    expect(texto('kpi-llamadas')).toContain('12');
    expect(texto('kpi-latencia')).toContain('91');
  });

  it('🎯 un mes SIN consumo muestra el vacío informativo, no el de error', () => {
    // Act — RF-APM-009: ceros son una respuesta válida
    consultar(reporte(0));

    // Assert
    const vacio = fixture.nativeElement.querySelector('app-list-empty-state');
    expect(vacio).toBeTruthy();
    expect(vacio.textContent).toContain('No es un error');
    expect(fixture.nativeElement.querySelector('app-list-error-state')).toBeNull();
  });

  it('un mes sin consumo NO ofrece «Reintentar»', () => {
    // Act
    consultar(reporte(0));

    // Assert — reintentar no cambiaría nada: la respuesta ya es correcta
    expect((fixture.nativeElement.textContent ?? '')).not.toContain('Reintentar');
  });

  describe('comparación', () => {
    it('sin marcar la casilla no hace la segunda llamada', () => {
      // Act
      consultar(reporte(12000));

      // Assert — no se compara contra cero por defecto
      http.expectNone((r) => r.url === '/api/v1/reportes-consumo');
    });

    it('con dos períodos muestra la variación', () => {
      // Arrange
      fixture.componentInstance.comparar.set(true);
      fixture.componentInstance.anioComparar.set(2026);
      fixture.componentInstance.mesComparar.set(6);

      // Act
      consultar(reporte(150));
      http
        .expectOne((r) => r.url === '/api/v1/reportes-consumo')
        .flush({ data: reporte(100, '2026-06'), meta: { pagination: null } });
      fixture.detectChanges();

      // Assert
      expect(texto('variacion')).toContain('+50');
      expect(texto('variacion')).toContain('50.0 %');
    });

    it('🎯 comparar contra un período de 0 llamadas NO da Infinity ni 100 %', () => {
      // Arrange
      fixture.componentInstance.comparar.set(true);

      // Act
      consultar(reporte(500));
      http
        .expectOne((r) => r.url === '/api/v1/reportes-consumo')
        .flush({ data: reporte(0, '2026-06'), meta: { pagination: null } });
      fixture.detectChanges();

      // Assert
      const v = texto('variacion');
      expect(v).toContain('Sin base de comparación');
      expect(v).not.toContain('Infinity');
      expect(v).not.toContain('100.0 %');
    });

    it('que falle la comparación no invalida el reporte principal', () => {
      // Arrange
      fixture.componentInstance.comparar.set(true);

      // Act
      consultar(reporte(500));
      http
        .expectOne((r) => r.url === '/api/v1/reportes-consumo')
        .flush(null, { status: 500, statusText: 'Server Error' });
      fixture.detectChanges();

      // Assert
      expect(texto('kpi-llamadas')).toContain('500');
    });
  });

  describe('período en la URL', () => {
    it('envía año y mes al backend tal como se eligieron', () => {
      // Act
      fixture.componentInstance.idpartner.set(12);
      fixture.componentInstance.anio.set(2026);
      fixture.componentInstance.mes.set(3);
      fixture.componentInstance.consultar();

      // Assert
      const req = http.expectOne((r) => r.url === '/api/v1/reportes-consumo');
      expect(req.request.params.get('anio')).toBe('2026');
      expect(req.request.params.get('mes')).toBe('3');
      req.flush({ data: reporte(10, '2026-03'), meta: { pagination: null } });
    });
  });

  it('sin partner elegido pide elegir uno y no llama al backend', () => {
    // Assert
    http.expectNone((r) => r.url === '/api/v1/reportes-consumo');
    expect(
      fixture.nativeElement.querySelector('app-list-empty-state').textContent,
    ).toContain('Elige un partner');
  });
});
