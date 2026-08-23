/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { PANTALLAS, informesDe } from '../definiciones/pantallas-oe1.definiciones';
import { PantallaZPage } from './pantalla-z.page';

function rutaDe(id: string) {
  return {
    url: of([{ path: id }]),
    snapshot: { url: [{ path: id }] },
  };
}

describe('PantallaZPage (OE1)', () => {
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

  function flushTodos(
    id: string,
    porInforme: Record<string, { data: unknown[]; meta?: Record<string, unknown>; status?: number }>,
  ) {
    for (const informe of informesDe(PANTALLAS[id])) {
      const req = http.expectOne((r) => r.url.endsWith(`/oe1/${informe}`));
      const cfg = porInforme[informe] ?? { data: [] };
      if (cfg.status) {
        req.flush({ detail: 'caída' }, { status: cfg.status, statusText: 'Error' });
      } else {
        req.flush({ data: cfg.data, meta: cfg.meta ?? {} });
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

  it('un_error_en_una_zona_deja_las_otras', () => {
    montar('ingreso');
    flushTodos('ingreso', {
      'mrr-mensual': {
        data: [{ mrr: 12000, recuento: 4 }],
        meta: { cobertura: 'parcial', falta: ['n=4'] },
      },
      'arr-proyeccion': { status: 500, data: [] },
      'tasa-renovacion': { data: [] },
    });
    expect(texto('zona-heroe')).toContain('12');
    expect(texto('zona-lectura')).toContain('caída');
  });

  it('ingreso_muestra_recuento_parcial_y_arr_extrapolado', () => {
    montar('ingreso');
    flushTodos('ingreso', {
      'mrr-mensual': {
        data: [{ mrr: 12000, recuento: 4 }],
        meta: { cobertura: 'parcial', falta: ['muestra n=4 bajo umbral 20'] },
      },
      'arr-proyeccion': {
        data: [{ arr: 144000, recuento: 4, escenario: 'extrapolacion_base' }],
        meta: { alcance: 'Extrapolación de MRR × 12; no es ingreso comprometido.' },
      },
      'tasa-renovacion': {
        data: [{ vencidas: 8, renovadas: 2, tasa_renovacion: 0.25 }],
      },
    });
    expect(texto('zona-heroe')).toContain('4');
    expect(texto('zona-parcial')).toContain('parcial');
    expect(texto('alcance-arr').toLowerCase()).toContain('extrapola');
    expect(texto('alcance-arr').toLowerCase()).toContain('no es ingreso comprometido');
    expect(html()).not.toContain('cac-por-canal');
    expect(html().toLowerCase()).not.toContain('mapa');
  });

  it('flujo_vacio_no_pinta_cero_euros', () => {
    montar('ingreso');
    flushTodos('ingreso', {});
    expect(texto('zona-heroe')).toContain('Sin datos');
    expect(texto('zona-heroe')).not.toContain('0 €');
  });

  it('cartera_agrupa_por_tipo_no_pais', () => {
    montar('cartera');
    flushTodos('cartera', {
      'cartera-por-plan': {
        data: [
          { plan: 'Pro', recuento: 3, pct_cartera: 0.75, mrr: 9000 },
          { plan: 'Base', recuento: 1, pct_cartera: 0.25, mrr: 3000 },
        ],
      },
      'mrr-por-segmento': {
        data: [
          { tipo: '(desconocido)', mrr: 3000, recuento: 1 },
          { tipo: 'empresa', mrr: 9000, recuento: 3 },
        ],
      },
    });
    expect(texto('zona-lectura')).toContain('desconocido');
    expect(texto('zona-lectura')).toContain('empresa');
    expect(html().toLowerCase()).not.toContain('mapa');
    expect(html()).not.toContain('cartera-mrr-por-mercado');
  });

  it('captacion_muestra_ceros_del_embudo', () => {
    montar('captacion');
    flushTodos('captacion', {
      'embudo-conversion': {
        data: [
          { etapa: 'lead', transiciones: 10 },
          { etapa: 'demo', transiciones: 0 },
        ],
        meta: { alcance: 'El cruce con Cuentas no aplica a este embudo comercial.' },
      },
      'velocidad-ciclo-venta': {
        data: [{ etapa: 'demo', idejecutivo: 7, segundos_promedio: 3600, transiciones: 2 }],
      },
    });
    expect(texto('zona-visual')).toContain('demo');
    expect(texto('zona-visual')).toContain('0');
    expect(html().toLowerCase()).not.toContain('@');
    expect(html().toLowerCase()).not.toContain('prospecto');
  });

  it('ciclo_n_bajo_sin_porcentaje_cerrado', () => {
    montar('ciclo');
    flushTodos('ciclo', {
      'churn-por-cohorte': {
        data: [{ cohorte_alta: '2026-01', n: 4, bajas: 1, pct_churn: null }],
      },
      'abandono-onboarding': {
        data: [
          { etapa: 'kickoff', clientes_completados: 2, orden: 1 },
          { etapa: 'go-live', clientes_completados: 0, orden: 2 },
        ],
      },
      'tiempo-onboarding': {
        data: [{ dias_mediana: 12, completados: 2, en_proceso: 1 }],
      },
    });
    expect(texto('zona-heroe')).toContain('4');
    expect(texto('zona-heroe')).not.toContain('25');
    expect(texto('zona-visual')).toContain('go-live');
    expect(texto('zona-lectura')).toContain('proceso');
    expect(html()).not.toContain('cac');
  });

  it('ninguna_pantalla_menciona_cac_ni_mercados', () => {
    for (const id of ['ingreso', 'cartera', 'captacion', 'ciclo']) {
      montar(id);
      flushTodos(id, {});
      const markup = html().toLowerCase();
      expect(markup).not.toContain('cac-por-canal');
      expect(markup).not.toContain('mercados-activos');
      expect(markup).not.toContain('cartera-mrr-por-mercado');
      http.verify();
    }
  });
});
