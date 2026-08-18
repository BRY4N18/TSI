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

function envelope(data: unknown[], meta: Record<string, unknown> = {}) {
  return { data, meta };
}

describe('PantallaZPage (Suscripciones)', () => {
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
    return http.expectOne((r) => r.url.endsWith(`/suscripciones/${informe}`));
  }

  function flushTodos(
    id: string,
    porInforme: Record<
      string,
      { data: unknown[]; meta?: Record<string, unknown>; status?: number }
    >,
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

  describe('Cobro e ingreso', () => {
    const cobroOk: Record<string, { data: unknown[]; meta?: Record<string, unknown> }> = {
      mrr: {
        data: [
          {
            mes: '2026-08',
            mrr: 347,
            nuevo: 149,
            expansion: 10,
            contraccion: -5,
            baja: -20,
            variacion_neta: 134,
            sin_periodicidad: 1,
            moneda: 'USD',
          },
        ],
        meta: {
          mes: '2026-07',
          nota_periodo: 'Se mide por mes natural; un rango arbitrario se resuelve al mes que lo contiene.',
        },
      },
      ingresos: {
        data: [
          {
            plan: 'Profesional',
            tipo_cliente: 'Empresa',
            facturado: 200,
            notas_credito: 40,
            ingreso_neto: 160,
            moneda: 'USD',
          },
        ],
      },
      'tasa-renovacion': {
        data: [{ vencidas: 4, renovadas: 2, pct_renovacion: 0.5 }],
      },
      'cobro-primer-intento': {
        data: [{ pagadas: 10, primer_intento: 7, tras_reintentos: 3, pct_primer_intento: 0.7 }],
      },
      'efectividad-dunning': {
        data: [{ escalon: 3, facturas_en_escalon: 4, recuperadas: 2, pct_recuperacion: 0.5 }],
        meta: { filtros: { escalones_dunning: '3,5' } },
      },
      'clientes-sin-metodo-pago': {
        data: [{ nombre_comercial: 'Acme', tipo: 'Empresa', estado_comercial: 'vigente', caduca_en_dias: 12 }],
      },
    };

    it('pinta_el_patron_Z_con_mes_natural', () => {
      montar('cobro');
      flushTodos('cobro', cobroOk);
      expect(texto('zona-heroe')).toBeTruthy();
      expect(texto('zona-periodo')).toBeTruthy();
      expect(texto('zona-mes')).toContain('2026-07');
      expect(texto('zona-visual')).toBeTruthy();
      expect(texto('zona-lectura')).toBeTruthy();
    });

    it('vacio_when_data_vacia_no_pinta_cero_por_ciento', () => {
      montar('cobro');
      flushTodos('cobro', {});
      expect(texto('zona-heroe')).toContain('Sin datos en este período');
      expect(texto('zona-heroe')).not.toContain('0.0 %');
      expect(texto('zona-heroe')).not.toContain('0 %');
    });

    it('sin_periodicidad_aparte_notas_credito_visibles_y_sin_enlace_a_metodos', () => {
      montar('cobro');
      flushTodos('cobro', cobroOk);
      expect(texto('sin-periodicidad')).toContain('sin periodicidad');
      expect(texto('notas-credito')).toContain('notas de crédito');
      expect(texto('notas-credito')).toContain('40');
      expect(html().toLowerCase()).not.toContain('/suscripciones/metodos-pago');
      expect(html().toLowerCase()).not.toContain('routerlink');
    });

    it('la_vista_principal_no_pasa_de_ocho_bloques_y_el_apoyo_nace_plegado', () => {
      montar('cobro');
      flushTodos('cobro', cobroOk);
      const bloques = fixture.nativeElement.querySelectorAll('[data-bloque-vista]');
      expect(bloques.length).toBeLessThanOrEqual(8);
      const apoyo = fixture.nativeElement.querySelector(
        '[data-testid="zona-apoyo"]',
      ) as HTMLDetailsElement;
      expect(apoyo.open).toBeFalse();
    });

    it('error_en_una_zona_no_vacia_el_heroe', () => {
      montar('cobro');
      flushTodos('cobro', {
        ...cobroOk,
        'efectividad-dunning': { data: [], status: 500 },
      });
      expect(texto('heroe-cifra')).toContain('347');
      expect(texto('zona-heroe')).not.toContain('caída');
    });

    it('cambiar_el_periodo_vuelve_a_pedir_todas_las_zonas', () => {
      montar('cobro');
      flushTodos('cobro', cobroOk);
      fixture.componentInstance.onPeriodoChange({ desde: '2026-01-01', hasta: '2026-01-31' });
      fixture.detectChanges();
      let pedidos = 0;
      for (const informe of informesDe(PANTALLAS['cobro'])) {
        const req = pedir(informe);
        expect(req.request.params.get('desde')).toBe('2026-01-01');
        req.flush(envelope([]));
        pedidos += 1;
      }
      expect(pedidos).toBe(6);
    });

    it('meta_mes_se_lee_aunque_el_rango_pedido_sea_otro', () => {
      montar('cobro');
      flushTodos('cobro', cobroOk);
      expect(texto('zona-mes')).toContain('2026-07');
      expect(texto('zona-mes')).toContain('mes natural');
    });
  });

  describe('Movimientos de cartera', () => {
    it('pendientes_aparte_mediana_nula_es_sin_dato_y_el_tipo_llega_tal_cual', () => {
      montar('movimientos');
      flushTodos('movimientos', {
        nrr: {
          data: [
            {
              nrr: 0.92,
              mrr_inicial: 400,
              expansion: 20,
              contraccion: -10,
              baja: -30,
              moneda: 'USD',
            },
          ],
          meta: { mes: '2026-08', nota_periodo: 'Se mide por mes natural.' },
        },
        'movimientos-plan': {
          data: [{ tipo_movimiento: 'downgrade', solicitudes: 1, delta_ingreso_total: -40 }],
        },
        'tiempo-resolucion-solicitudes': {
          data: [{ resueltas: 2, pendientes: 3, segundos_mediana: null }],
        },
        'suspension-reactivacion': {
          data: [{ suspendidas: 1, reactivadas: 1, pct_suspension: 0.1, pct_reactivacion: 0.1 }],
        },
      });
      expect(texto('zona-mes')).toContain('2026-08');
      expect(texto('pendientes')).toContain('pendientes');
      expect(texto('mediana-ausente')).toContain('sin dato');
      expect(texto('tipo-movimiento')).toContain('downgrade');
      expect(html().toLowerCase()).not.toContain('administrador');
    });

    it('error_en_suspension_no_vacia_el_heroe', () => {
      montar('movimientos');
      flushTodos('movimientos', {
        nrr: {
          data: [{ nrr: 0.8, mrr_inicial: 100, expansion: 0, contraccion: 0, baja: -20 }],
          meta: { mes: '2026-08' },
        },
        'movimientos-plan': { data: [] },
        'tiempo-resolucion-solicitudes': { data: [] },
        'suspension-reactivacion': { data: [], status: 500 },
      });
      expect(texto('heroe-cifra')).toContain('80.0 %');
    });
  });

  describe('Catálogo y uso', () => {
    it('plan_precio_cero_aparece_con_ambos_numeros_y_sin_columna_de_llamadas', () => {
      montar('catalogo');
      flushTodos('catalogo', {
        'distribucion-cartera': {
          data: [
            { plan: 'Demo', nivel: 0, clientes: 2, pct_clientes: 0.5, mrr_aportado: 0, pct_ingreso: 0 },
            { plan: 'Pro', nivel: 1, clientes: 2, pct_clientes: 0.5, mrr_aportado: 200, pct_ingreso: 1 },
          ],
        },
        'utilizacion-limites': {
          data: [
            {
              plan: 'Pro',
              unidades_usadas: 5,
              unidades_limite: 25,
              usuarios_usados: 2,
              usuarios_limite: 10,
              nota_dimension_pendiente: 'La dimensión de llamadas se incorporará con Partners.',
            },
          ],
        },
        'severidades-habilitadas-vs-usadas': {
          data: [{ plan: 'Pro', severidad: 'grave', habilitada: true, casos_atendidos: 0 }],
        },
      });
      expect(texto('plan-precio-cero')).toContain('Demo');
      expect(texto('plan-precio-cero')).toContain('2 clientes');
      expect(texto('utilizado-contratado')).toContain('5 de 25');
      expect(texto('nota-dimension-pendiente')).toContain('dimensión');
      expect(texto('severidad-sin-uso')).toContain('habilitada y no usada');
      expect(fixture.nativeElement.querySelector('[data-testid="zona-mes"]')).toBeNull();
      const markup = html().toLowerCase();
      expect(markup).not.toContain('cac');
      expect(fixture.nativeElement.querySelector('[data-campo="llamadas"]')).toBeNull();
      expect(markup).not.toMatch(/<th[^>]*>\s*llamadas/);
    });

    it('vacio_when_data_vacia_no_pinta_cero_por_ciento', () => {
      montar('catalogo');
      flushTodos('catalogo', {});
      expect(texto('zona-heroe')).toContain('Sin datos en este período');
      expect(texto('zona-heroe')).not.toContain('0.0 %');
    });
  });

  it('no_hay_mapa_exportar_ni_cta_operativa', () => {
    montar('cobro');
    flushTodos('cobro', {});
    const markup = html().toLowerCase();
    expect(markup).not.toContain('leaflet');
    expect(markup).not.toContain('exportar');
    expect(markup).not.toContain('emitir');
    expect(markup).not.toContain('cambiar plan');
    expect(markup).not.toContain('llamadas');
    expect(markup).not.toContain('metodos-pago');
  });
});
