/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { PANTALLAS, informesDe } from '../definiciones/pantallas-oe3.definiciones';
import { PantallaZPage } from './pantalla-z.page';

function rutaDe(id: string) {
  return {
    url: of([{ path: id }]),
    snapshot: { url: [{ path: id }] },
  };
}

describe('PantallaZPage (OE3)', () => {
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
      const req = http.expectOne((r) => r.url.endsWith(`/oe3/${informe}`));
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

  it('cambiar_comparacion_vuelve_a_pedir', () => {
    montar('latencia');
    flushTodos('latencia', {});
    fixture.componentInstance.comparacion = 'mom';
    fixture.componentInstance.onFiltrosChange();
    fixture.detectChanges();
    for (const informe of informesDe(PANTALLAS['latencia'])) {
      const req = http.expectOne((r) => r.url.endsWith(`/oe3/${informe}`));
      expect(req.request.params.get('comparacion')).toBe('mom');
      req.flush({ data: [], meta: {} });
    }
    fixture.detectChanges();
  });

  it('un_error_en_una_zona_deja_las_otras', () => {
    montar('latencia');
    flushTodos('latencia', {
      'latencia-asignacion': {
        data: [{ p95_min: 1.8, casos_asignados: 40, excluidos_sin_asignacion: 2 }],
        meta: {
          cobertura: 'parcial',
          falta: ['n=40'],
          objetivo: { cumple: true },
          alcance: 'Mide minutos del proceso registro→asignación, no milisegundos de algoritmo.',
        },
      },
      'evolucion-latencia': { status: 500, data: [] },
    });
    expect(texto('zona-heroe')).toContain('1.8');
    expect(texto('zona-visual')).toContain('caída');
  });

  it('latencia_muestra_p95_recuento_y_cumple', () => {
    montar('latencia');
    flushTodos('latencia', {
      'latencia-asignacion': {
        data: [{ p95_min: 1.8, casos_asignados: 40, excluidos_sin_asignacion: 2 }],
        meta: {
          cobertura: 'parcial',
          objetivo: { cumple: true },
          alcance: 'Mide minutos del proceso registro→asignación, no milisegundos de algoritmo.',
        },
      },
      'evolucion-latencia': {
        data: [{ periodo: '2026-07', p95_min: 1.9, casos_asignados: 12 }],
      },
    });
    expect(texto('zona-heroe')).toContain('1.8');
    expect(texto('zona-heroe')).toContain('40');
    expect(texto('zona-heroe')).toContain('cumple');
    expect(texto('zona-parcial')).toContain('parcial');
    expect(texto('alcance-proceso').toLowerCase()).toContain('proceso');
    expect(html().toLowerCase()).not.toContain('100 ms');
    expect(html().toLowerCase()).not.toContain('leaflet');
  });

  it('flujo_vacio_no_pinta_cero_min_ni_meta_cumplida', () => {
    montar('latencia');
    flushTodos('latencia', {});
    expect(texto('zona-heroe')).toContain('Sin despachos');
    expect(texto('zona-heroe')).not.toContain('0 min');
    expect(texto('zona-heroe').toLowerCase()).not.toContain('cumple');
  });

  it('p95_nulo_se_lee_sin_dato', () => {
    montar('latencia');
    flushTodos('latencia', {
      'latencia-asignacion': {
        data: [{ p95_min: null, casos_asignados: 3, excluidos_sin_asignacion: 0 }],
      },
      'evolucion-latencia': { data: [] },
    });
    expect(texto('zona-heroe').toLowerCase()).toContain('sin dato');
  });

  it('calidad_campos_y_sin_semaforo_e3_11', () => {
    montar('calidad');
    flushTodos('calidad', {
      'tasa-error-registro': {
        data: [
          {
            tasa_error: 0,
            incompletos: 0,
            casos: 20,
            campos_comprobados: 'severidad, condado',
          },
        ],
        meta: { objetivo: { cumple: true } },
      },
      'primer-intento': {
        data: [{ pct_primer_intento: 0.9, resueltos_primer_intento: 18, casos: 20 }],
        meta: { objetivo: { cumple: null } },
      },
    });
    expect(texto('campos-comprobados')).toContain('severidad');
    expect(texto('zona-visual')).toContain('20');
    expect(texto('zona-visual').toLowerCase()).not.toContain('cumple');
    expect(texto('zona-visual').toLowerCase()).not.toContain('no cumple');
  });

  it('capacidad_sin_capacidad_no_es_infinito_ni_mapa', () => {
    montar('capacidad');
    flushTodos('capacidad', {
      'ratio-demanda-capacidad': {
        data: [
          { condado: 'Orange', casos: 8, unidades_vigentes: 2, ratio: 4, sin_capacidad: 0 },
          { condado: 'Lee', casos: 5, unidades_vigentes: 0, ratio: null, sin_capacidad: 1 },
        ],
        meta: { alcance: 'La capacidad es la flota vigente en el período, no la de hoy.' },
      },
      'perdida-de-senal': {
        data: [{ unidad: 'U-1', huecos: 2, intervalos_medidos: 40, pct_huecos: 0.05 }],
      },
    });
    expect(texto('zona-heroe')).toContain('sin capacidad');
    expect(texto('zona-heroe')).not.toContain('Infinity');
    expect(texto('alcance-flota').toLowerCase()).toContain('período');
    expect(html().toLowerCase()).not.toContain('leaflet');
    expect(html().toLowerCase()).not.toContain('latitud');
  });

  it('respaldo_tasa_con_denominador_vacio_no_es_cero_pct', () => {
    montar('respaldo');
    flushTodos('respaldo', {
      'cobertura-de-respaldo': {
        data: [
          {
            condado: 'Orange',
            vecinos: 10,
            vecinos_con_unidad_disponible: 4,
            pct_respaldo: 0.4,
          },
        ],
      },
    });
    expect(texto('zona-heroe')).toContain('10');
    expect(texto('zona-heroe')).toContain('4');

    montar('respaldo');
    flushTodos('respaldo', {});
    expect(texto('zona-heroe').toLowerCase()).toContain('sin pares');
    expect(texto('zona-heroe')).not.toContain('0 %');
  });

  it('ninguna_pantalla_menciona_mapa_region_bloqueados', () => {
    for (const id of ['latencia', 'calidad', 'capacidad', 'respaldo']) {
      montar(id);
      flushTodos(id, {});
      const markup = html().toLowerCase();
      expect(markup).not.toContain('leaflet');
      expect(markup).not.toContain('data-testid="mapa"');
      expect(markup).not.toContain('uptime-por-region');
      expect(markup).not.toContain('20000');
      http.verify();
    }
  });
});
