/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { PANTALLAS, informesDe } from '../definiciones/pantallas-oe2.definiciones';
import { PantallaZPage } from './pantalla-z.page';

function rutaDe(id: string) {
  return {
    url: of([{ path: id }]),
    snapshot: { url: [{ path: id }] },
  };
}

describe('PantallaZPage (OE2)', () => {
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
      const req = http.expectOne((r) => r.url.endsWith(`/oe2/${informe}`));
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
    montar('uso');
    flushTodos('uso', {
      'integraciones-activas': {
        data: [{ pct_adopcion: 0.5, partners_con_llamada: 2, partners_con_acceso: 4 }],
      },
      'consumo-por-partner': { status: 500, data: [] },
      'taxonomia-errores': { data: [] },
      'latencia-por-endpoint': { data: [] },
    });
    expect(texto('zona-heroe')).toContain('50');
    expect(texto('zona-lectura')).toContain('caída');
  });

  it('uso_no_pinta_cero_ms_en_vacio', () => {
    montar('uso');
    flushTodos('uso', {});
    expect(texto('zona-heroe')).toContain('Sin datos');
    expect(texto('zona-heroe')).not.toContain('0 ms');
  });

  it('taxonomia_no_suma_clases_y_consumo_muestra_cero', () => {
    montar('uso');
    flushTodos('uso', {
      'integraciones-activas': {
        data: [{ pct_adopcion: 0.5, partners_con_llamada: 2, partners_con_acceso: 4 }],
      },
      'taxonomia-errores': {
        data: [
          { clase_http: '4xx', llamadas: 3, denominador: 18, pct: 0.16 },
          { clase_http: '5xx', llamadas: 1, denominador: 18, pct: 0.05 },
        ],
      },
      'consumo-por-partner': {
        data: [
          { partner: 'Con trafico', llamadas: 5, cupo: 100 },
          { partner: 'Sin trafico', llamadas: 0, cupo: 100 },
        ],
      },
      'latencia-por-endpoint': {
        data: [
          {
            endpoint_path: '/v1/x',
            latencia_p95_ms: 90,
            latencia_media_ms: 80,
            muestras: 5,
            percentil_fiable: 0,
          },
        ],
      },
    });
    expect(texto('zona-visual')).toContain('4xx');
    expect(texto('zona-visual')).toContain('5xx');
    expect(html().toLowerCase()).not.toContain('errores totales');
    expect(texto('zona-lectura')).toContain('Sin trafico');
    expect(html()).not.toContain('disponibilidad');
    expect(html().toLowerCase()).not.toContain('uptime');
    expect(html()).not.toContain('/partners/gestion/consumo');
  });

  it('dinero_muestra_componentes_alcance_y_no_tarificable', () => {
    montar('dinero');
    flushTodos('dinero', {
      'excedente-facturable': {
        data: [
          {
            partner: 'A',
            llamadas: 30,
            cupo: 20,
            precio_unitario: 0.05,
            importe_facturable: 0.5,
            no_tarificable: 0,
          },
          {
            partner: 'B',
            llamadas: 5,
            cupo: 100,
            precio_unitario: null,
            importe_facturable: null,
            no_tarificable: 1,
          },
        ],
        meta: { alcance: 'Importe facturable. No afirma cobro.' },
      },
      'participacion-ingresos-api': {
        data: [{ llamadas: 18 }],
        meta: { cobertura: 'parcial', falta: ['precio del plan de API'] },
      },
      'mrr-por-linea': {
        data: [{ linea: 'plataforma', monto: 10 }],
        meta: { cobertura: 'parcial', falta: ['precio del plan de API'] },
      },
    });
    expect(texto('zona-heroe')).toContain('30');
    expect(texto('zona-heroe')).toContain('20');
    expect(texto('alcance-facturable')).toContain('No afirma cobro');
    expect(texto('zona-visual')).toContain('B');
    expect(html().toLowerCase()).not.toContain('uptime');
  });

  it('ecosistema_dos_v1_y_sin_contacto', () => {
    montar('ecosistema');
    flushTodos('ecosistema', {
      'crecimiento-ecosistema': { data: [{ partners_nuevos: 1 }] },
      'adopcion-versiones': {
        data: [
          { servicio: 'datos', version: 'v1', llamadas: 10, version_es_derivada: 1 },
          { servicio: 'despacho', version: 'v1', llamadas: 8, version_es_derivada: 1 },
        ],
      },
      'comparativa-partners': {
        data: [
          { partner: 'Activo', llamadas: 10 },
          { partner: 'Silencio', llamadas: 0 },
        ],
      },
    });
    const visual = texto('zona-visual');
    expect(visual).toContain('datos');
    expect(visual).toContain('despacho');
    expect(texto('version-derivada').toLowerCase()).toContain('deriv');
    expect(texto('zona-lectura')).toContain('Silencio');
    expect(html()).not.toContain('contacto');
    expect(html()).not.toContain('client_secret');
  });
});
