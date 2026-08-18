/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { informesDe, PANTALLAS } from '../definiciones/pantallas-gestion.definiciones';
import { PantallaZPage } from './pantalla-z.page';

function rutaDe(id: string) {
  return {
    url: of([{ path: id }]),
    snapshot: { url: [{ path: id }] },
  };
}

function envelope(
  resultados: unknown[],
  meta: Record<string, unknown> = {},
) {
  return { data: { resultados }, meta };
}

describe('PantallaZPage (Partners)', () => {
  let fixture: ComponentFixture<PantallaZPage>;
  let http: HttpTestingController;

  function montar(id: string) {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [PantallaZPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ActivatedRoute, useValue: rutaDe(id) },
      ],
    });
    fixture = TestBed.createComponent(PantallaZPage);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  }

  function pedir(informe: string) {
    return http.expectOne((r) => r.url.endsWith(`/partners/${informe}`));
  }

  function flushTodos(
    id: string,
    porInforme: Record<string, { data: unknown[]; meta?: Record<string, unknown>; status?: number }>,
  ) {
    for (const informe of informesDe(PANTALLAS[id])) {
      const req = pedir(informe);
      const cfg = porInforme[informe] ?? { data: [] };
      if (cfg.status) {
        req.flush({ detail: 'caída' }, { status: cfg.status, statusText: 'Error' });
      } else {
        req.flush(envelope(cfg.data, cfg.meta ?? {}));
      }
    }
    fixture.detectChanges();
  }

  function texto(testid: string): string {
    const el = fixture.nativeElement.querySelector(`[data-testid="${testid}"]`);
    return el ? (el.textContent as string).replace(/\s+/g, ' ').trim() : '';
  }

  function html(): string {
    return (fixture.nativeElement as HTMLElement).innerHTML;
  }

  afterEach(() => {
    http?.verify();
  });

  describe('cáscara', () => {
    it('un_error_en_una_zona_deja_las_otras_visibles', () => {
      montar('consumo');
      flushTodos('consumo', {
        'latencia-p95': {
          data: [
            {
              endpoint_path: '/api/v1/datos/accidentes',
              latencia_p95_ms: 90,
              latencia_media_ms: 80,
              muestras: 18,
              percentil_fiable: 0,
            },
          ],
          meta: { nota_muestras: 'Hay medidas calculadas sobre pocas llamadas.' },
        },
        comparativa: { status: 500, data: [] },
        'taxonomia-errores': { data: [] },
        'metricas-consumo': { data: [] },
        'reporte-mensual-consumo': { data: [] },
        'consumo-por-endpoint': { data: [] },
        'participacion-ingresos-api': { data: [] },
      });
      expect(texto('zona-heroe')).toContain('ms p95');
      expect(texto('zona-lectura')).toContain('caída');
    });
  });

  describe('Consumo', () => {
    const ok = {
      'latencia-p95': {
        data: [
          {
            endpoint_path: '/api/v1/datos/accidentes',
            latencia_p95_ms: 90,
            latencia_media_ms: 80,
            muestras: 5,
            percentil_fiable: 0,
          },
        ],
        meta: { nota_muestras: 'Hay medidas calculadas sobre pocas llamadas.' },
      },
      'taxonomia-errores': {
        data: [
          { clase_resultado: 'limite_cupo', codigo_http: 429, llamadas: 3, pct: 0.5 },
          { clase_resultado: 'autorizacion', codigo_http: 403, llamadas: 2, pct: 0.33 },
          { clase_resultado: 'error_servicio', codigo_http: 500, llamadas: 1, pct: 0.17 },
        ],
      },
      comparativa: {
        data: [
          { partner: 'Con trafico', llamadas: 5, pct_error: 0.2, latencia_p95_ms: 90 },
          { partner: 'Sin trafico', llamadas: 0, pct_error: null, latencia_p95_ms: null },
        ],
      },
      'metricas-consumo': { data: [] },
      'reporte-mensual-consumo': { data: [] },
      'consumo-por-endpoint': { data: [] },
      'participacion-ingresos-api': {
        data: [{ partner: 'Acme', ingreso_base: 100, excedente: 20, pct_excedente: 0.17 }],
      },
    };

    it('el_trio_viaja_en_el_heroe_y_la_fila_no_fiable_sigue', () => {
      montar('consumo');
      flushTodos('consumo', ok);
      const heroe = texto('zona-heroe');
      expect(heroe).toContain('90');
      expect(heroe).toContain('80');
      expect(heroe).toContain('5');
      expect(texto('marca-no-fiable')).toContain('no fiable');
      expect(texto('zona-nota-muestras')).toContain('pocas llamadas');
      expect(fixture.nativeElement.querySelectorAll('[data-bloque-vista]').length).toBeLessThanOrEqual(
        8,
      );
    });

    it('vacio_when_resultados_vacios_no_pinta_cero_ms', () => {
      montar('consumo');
      flushTodos('consumo', {});
      expect(texto('zona-heroe')).toContain('Sin datos');
      expect(texto('zona-heroe')).not.toContain('0 ms');
    });

    it('comparativa_pinta_partner_en_cero_y_no_suma_clases', () => {
      montar('consumo');
      flushTodos('consumo', ok);
      expect(texto('zona-lectura')).toContain('Sin trafico');
      expect(texto('zona-lectura')).toContain('0 llamadas');
      expect(html()).not.toContain('escalados');
      expect(html().toLowerCase()).not.toContain('leaflet');
      expect(html()).not.toContain('/partners/consola/logs');
      expect(html()).not.toContain('/partners/portal/consumo');
    });

    it('cambiar_el_periodo_vuelve_a_pedir_todas_las_zonas', () => {
      montar('consumo');
      flushTodos('consumo', ok);
      fixture.componentInstance.onPeriodoChange({ desde: '2026-07-01', hasta: '2026-07-31' });
      flushTodos('consumo', ok);
      expect(texto('zona-heroe')).toContain('ms p95');
    });
  });

  describe('Incorporación', () => {
    it('dos_v1_no_se_colapsan_y_en_proceso_no_es_cero_dias', () => {
      montar('incorporacion');
      flushTodos('incorporacion', {
        'adopcion-versiones': {
          data: [
            { servicio: 'datos', version: 'v1', llamadas: 10, pct: 0.5, version_es_derivada: 1 },
            { servicio: 'despacho', version: 'v1', llamadas: 10, pct: 0.5, version_es_derivada: 1 },
          ],
        },
        'motivo-credencial-inactiva': {
          data: [
            { partner: 'A', motivo_inactividad: 'revocada', credenciales: 1, pct: 0.5 },
            { partner: 'A', motivo_inactividad: 'expirada', credenciales: 1, pct: 0.5 },
          ],
        },
        'tiempo-incorporacion': {
          data: [{ partner: 'Aún', etapa: 'registro', dias: null, en_proceso: 1 }],
        },
        'tasa-rechazo-produccion': { data: [] },
      });
      const heroe = texto('zona-heroe');
      expect(heroe).toContain('datos v1');
      expect(heroe).toContain('despacho v1');
      expect(texto('version-derivada')).toContain('deriva');
      expect(texto('zona-visual')).toContain('revocada');
      expect(texto('zona-visual')).toContain('expirada');
      expect(texto('zona-lectura')).toContain('en proceso');
      expect(texto('zona-lectura')).not.toContain('0 días');
      expect(html()).not.toContain('ejecutado_por');
    });
  });

  describe('Entrega', () => {
    it('un_solo_get_alimenta_heroe_y_lectura_y_no_hay_mapa', () => {
      montar('entrega');
      const pedidos: string[] = [];
      http.match((r) => r.url.includes('/partners/')).forEach((req) => {
        pedidos.push(req.request.url);
        if (req.request.url.endsWith('clientes-integracion-activa')) {
          req.flush(
            envelope([
              {
                periodo: '2026-08-01',
                clientes_totales: 10,
                con_integracion: 2,
                pct: 0.2,
                meta: 0.7,
              },
            ]),
          );
        } else {
          req.flush(
            envelope([
              { cliente: '(portal)', canal: 'portal', expedientes: 4 },
              { cliente: '1', canal: 'api', expedientes: 2 },
            ]),
          );
        }
      });
      fixture.detectChanges();
      expect(pedidos.filter((u) => u.endsWith('clientes-integracion-activa')).length).toBe(1);
      expect(texto('zona-heroe')).toContain('20.0 %');
      expect(texto('zona-heroe')).toContain('70.0 %');
      expect(texto('implicacion-cien')).toContain('100 %');
      expect(texto('zona-visual')).toContain('portal');
      expect(texto('zona-visual')).toContain('api');
      expect(html().toLowerCase()).not.toContain('leaflet');
      expect(html()).not.toContain('fuera de zona');
    });
  });
});
