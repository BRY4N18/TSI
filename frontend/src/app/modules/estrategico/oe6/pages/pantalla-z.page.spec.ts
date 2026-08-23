/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { PANTALLAS, informesDe } from '../definiciones/pantallas-oe6.definiciones';
import { PantallaZPage } from './pantalla-z.page';

function rutaDe(id: string) {
  return {
    url: of([{ path: id }]),
    snapshot: { url: [{ path: id }] },
  };
}

describe('PantallaZPage (OE6)', () => {
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
      const req = http.expectOne((r) => r.url.endsWith(`/oe6/${informe}`));
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
    montar('llegada');
    flushTodos('llegada', {});
    fixture.componentInstance.comparacion = 'mom';
    fixture.componentInstance.onFiltrosChange();
    fixture.detectChanges();
    for (const informe of informesDe(PANTALLAS['llegada'])) {
      const req = http.expectOne((r) => r.url.endsWith(`/oe6/${informe}`));
      expect(req.request.params.get('comparacion')).toBe('mom');
      req.flush({ data: [], meta: {} });
    }
    fixture.detectChanges();
  });

  it('un_error_en_una_zona_deja_las_otras', () => {
    montar('llegada');
    flushTodos('llegada', {
      'tiempo-respuesta-global': {
        data: [{ mediana_min: 9, p95_min: 18, casos_con_llegada: 40, excluidos_sin_llegada: 3 }],
        meta: { cobertura: 'parcial', falta: ['n=40'] },
      },
      'tiempo-respuesta-por-severidad': { status: 500, data: [] },
    });
    expect(texto('zona-heroe')).toContain('9');
    expect(texto('zona-visual')).toContain('caída');
  });

  it('llegada_muestra_mediana_p95_y_recuento', () => {
    montar('llegada');
    flushTodos('llegada', {
      'tiempo-respuesta-global': {
        data: [{ mediana_min: 9, p95_min: 18, casos_con_llegada: 40, excluidos_sin_llegada: 3 }],
        meta: { cobertura: 'parcial' },
      },
      'tiempo-respuesta-por-severidad': {
        data: [{ severidad: 'Grave', mediana_min: 11, p95_min: 22, casos: 12 }],
      },
    });
    expect(texto('zona-heroe')).toContain('9');
    expect(texto('zona-heroe')).toContain('18');
    expect(texto('zona-heroe')).toContain('40');
    expect(texto('zona-parcial')).toContain('parcial');
    expect(texto('zona-lectura')).toContain('3');
    expect(html().toLowerCase()).not.toContain('leaflet');
    expect(html().toLowerCase()).not.toContain('eta');
  });

  it('flujo_vacio_no_pinta_cero_min', () => {
    montar('llegada');
    flushTodos('llegada', {});
    expect(texto('zona-heroe')).toContain('Sin casos');
    expect(texto('zona-heroe')).not.toContain('0 min');
  });

  it('p95_nulo_se_lee_sin_dato', () => {
    montar('llegada');
    flushTodos('llegada', {
      'tiempo-respuesta-global': {
        data: [{ mediana_min: 9, p95_min: null, casos_con_llegada: 3, excluidos_sin_llegada: 0 }],
      },
      'tiempo-respuesta-por-severidad': { data: [] },
    });
    expect(texto('zona-heroe')).toContain('sin dato');
    expect(texto('zona-heroe')).toContain('9');
  });

  it('diagnostico_no_titula_eta', () => {
    montar('diagnostico');
    flushTodos('diagnostico', {
      'tramos-del-ciclo': {
        data: [{ tramo: 'asignacion_a_llegada', mediana_min: 6, casos: 20 }],
      },
      'origen-de-asignacion': {
        data: [{ origen: 'automatico', pct: 0.7, despachos: 14 }],
      },
      'desviacion-de-llegada': {
        data: [{ desviacion_mediana: 90, llegadas_medidas: 20 }],
        meta: { alcance: 'La referencia es el histórico comparable, no un ETA estimado.' },
      },
    });
    expect(texto('zona-heroe')).toContain('asignacion_a_llegada');
    expect(texto('alcance-historico').toLowerCase()).toContain('histórico');
    expect(texto('alcance-historico').toLowerCase()).toContain('no un eta');
  });

  it('ejecucion_tasas_con_denominador', () => {
    montar('ejecucion');
    flushTodos('ejecucion', {
      'envejecimiento-de-casos-abiertos': {
        data: [{ tramo_dias: '0-1', casos_abiertos: 4 }],
      },
      'rechazo-y-timeout-por-unidad': {
        data: [{ unidad: 'U-1', rechazados: 2, ofrecidos: 10, tasa_rechazo: 0.2 }],
      },
      'abortos-y-misiones-fallidas': { data: [] },
      'cierres-forzados': {
        data: [{ forzados: 1, despachos_confirmados: 20, pct_forzados: 0.05 }],
        meta: { alcance: 'Cierres forzados: definición de despacho, no retiro manual.' },
      },
    });
    expect(texto('zona-visual')).toContain('10');
    expect(texto('alcance-cierres').toLowerCase()).toContain('definición');
  });

  it('personas_no_finge_ceros_ni_identidad', () => {
    montar('personas');
    flushTodos('personas', {
      'impacto-humano': {
        data: [{ victimas: 5, heridos: 4, fallecidos: 1, casos_con_dato: 8, casos: 12 }],
      },
      'escaladas-de-severidad': {
        data: [{ con_escalada: 1, casos: 12, sin_medir: 9 }],
        meta: { cobertura: 'parcial', falta: ['muestra escasa'] },
      },
      'cobertura-de-evidencia': {
        data: [{ pct_con_ambas: 0.4, casos_cerrados: 10 }],
      },
    });
    expect(texto('zona-heroe')).toContain('5');
    expect(texto('zona-parcial')).toContain('parcial');
    expect(html().toLowerCase()).not.toContain('nombre');
    expect(html().toLowerCase()).not.toContain('latitud');
  });

  it('ninguna_pantalla_menciona_mapa_eta_oe3', () => {
    for (const id of ['llegada', 'diagnostico', 'ejecucion', 'personas']) {
      montar(id);
      flushTodos(id, {});
      const markup = html().toLowerCase();
      expect(markup).not.toContain('leaflet');
      expect(markup).not.toContain('latencia-asignacion');
      expect(markup).not.toContain('data-testid="mapa"');
      http.verify();
    }
  });
});
