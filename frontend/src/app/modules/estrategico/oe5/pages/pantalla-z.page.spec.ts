/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { PANTALLAS, informesDe } from '../definiciones/pantallas-oe5.definiciones';
import { PantallaZPage } from './pantalla-z.page';

function rutaDe(id: string) {
  return {
    url: of([{ path: id }]),
    snapshot: { url: [{ path: id }] },
  };
}

describe('PantallaZPage (OE5)', () => {
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
      const req = http.expectOne((r) => r.url.endsWith(`/oe5/${informe}`));
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
    montar('servicio');
    flushTodos('servicio', {
      'cumplimiento-sla': {
        data: [{ pct_cumplimiento: 0.93, con_compromiso: 14, sin_compromiso: 2 }],
        meta: { cobertura: 'parcial', falta: ['n=14'] },
      },
      'evolucion-incumplimiento': { status: 500, data: [] },
      'rendimiento-por-agente': { data: [] },
      'reincidencia-soporte': { data: [] },
    });
    expect(texto('zona-heroe')).toContain('14');
    expect(texto('zona-visual')).toContain('caída');
  });

  it('servicio_muestra_recuento_parcial_y_no_cero_si_vacio', () => {
    montar('servicio');
    flushTodos('servicio', {
      'cumplimiento-sla': {
        data: [{ pct_cumplimiento: 0.93, con_compromiso: 14, sin_compromiso: 2 }],
        meta: { cobertura: 'parcial', falta: ['muestra n=14 bajo umbral 20'] },
      },
      'evolucion-incumplimiento': { data: [{ periodo: '2026-08', pct_incumplimiento: 0.07, incumplidos: 1 }] },
      'rendimiento-por-agente': { data: [{ idagente: 3, asignados: 8, resueltos: 5 }] },
      'reincidencia-soporte': { data: [{ idcliente: 9, servicio: 'api', tickets: 3 }] },
    });
    expect(texto('zona-heroe')).toContain('14');
    expect(texto('zona-parcial')).toContain('parcial');
    expect(html().toLowerCase()).not.toContain('nps');
    expect(html().toLowerCase()).not.toContain('ticket #');
  });

  it('flujo_vacio_no_pinta_cero_porciento', () => {
    montar('servicio');
    flushTodos('servicio', {});
    expect(texto('zona-heroe')).toContain('Sin compromisos');
    expect(texto('zona-heroe')).not.toContain('0 %');
  });

  it('ingresos_descompone_nrr', () => {
    montar('ingresos');
    flushTodos('ingresos', {
      'retencion-neta-ingresos': {
        data: [{ nrr: 1.05, expansion: 200, contraccion: 50, churn: 80, recuento: 4 }],
        meta: { alcance: 'NRR descompuesto; precio congelado en la suscripción, no el catálogo.' },
      },
    });
    expect(texto('zona-visual')).toContain('Expansión');
    expect(texto('zona-visual')).toContain('Contracción');
    expect(texto('zona-visual')).toContain('Churn');
    expect(texto('alcance-nrr').toLowerCase()).toContain('congelado');
    expect(html().toLowerCase()).not.toContain('expansión = 0');
  });

  it('planes_solo_aprobados_y_activas', () => {
    montar('planes');
    flushTodos('planes', {
      'sla-por-plan': {
        data: [{ plan: 'Pro', pct_cumplimiento: 0.97, con_compromiso: 10 }],
      },
      'movimientos-de-plan': {
        data: [{ tipo_movimiento: 'upgrade', recuento: 1, delta_ingreso: 40 }],
      },
      'antiguedad-de-cuenta': {
        data: [{ activas: 4, cerradas: 1, dias_antiguedad_media: 120 }],
      },
    });
    expect(texto('zona-visual')).toContain('upgrade');
    expect(texto('zona-lectura')).toContain('Activas');
    expect(texto('zona-lectura')).toContain('Cerradas');
  });

  it('riesgo_una_senal_no_basta_y_falta_se_nombra', () => {
    montar('riesgo');
    flushTodos('riesgo', {
      'cuentas-en-riesgo': {
        data: [{ idcliente: 2, n_senales: 2, senal_api: 1, senal_tickets: 1, senal_cobro: 0, senal_sesiones: 0 }],
        meta: { alcance: 'Una cuenta se marca solo con dos o más señales.', falta: ['sesiones'] },
      },
    });
    expect(texto('zona-heroe')).toContain('1');
    expect(texto('zona-visual')).toContain('2 señales');
    expect(texto('zona-lectura')).toContain('sesiones');
    expect(html().toLowerCase()).not.toContain('latitud');
  });

  it('ninguna_pantalla_menciona_nps_ni_ciclo_oe1', () => {
    for (const id of ['servicio', 'ingresos', 'planes', 'riesgo']) {
      montar(id);
      flushTodos(id, {});
      const markup = html().toLowerCase();
      expect(markup).not.toContain('nps-satisfaccion');
      expect(markup).not.toContain('reportes-sin-correccion');
      expect(markup).not.toContain('tasa-renovacion');
      expect(markup).not.toContain('churn-por-cohorte');
      http.verify();
    }
  });
});
