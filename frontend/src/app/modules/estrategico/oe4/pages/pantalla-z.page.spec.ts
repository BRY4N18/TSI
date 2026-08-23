/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { PANTALLAS, informesDe } from '../definiciones/pantallas-oe4.definiciones';
import { PantallaZPage } from './pantalla-z.page';

function rutaDe(id: string) {
  return { url: of([{ path: id }]), snapshot: { url: [{ path: id }] } };
}

describe('PantallaZPage (OE4)', () => {
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
      const req = http.expectOne((r) => r.url.endsWith(`/oe4/${informe}`));
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

  afterEach(() => http?.verify());

  it('error_en_una_zona_deja_las_otras', () => {
    montar('calidad');
    flushTodos('calidad', {
      'indice-calidad-historico': {
        data: [
          {
            indice_consolidado: 0.7,
            pct_completitud: 0.8,
            pct_descarte: 0.1,
            pct_fusion: 0.05,
            pct_cobertura_evidencia: 0.01,
          },
        ],
      },
      'completitud-campos-criticos': { status: 500, data: [] },
    });
    expect(texto('zona-heroe')).toContain('70');
    expect(texto('zona-visual')).toContain('caída');
  });

  it('calidad_muestra_indice_y_cuatro_piezas', () => {
    montar('calidad');
    flushTodos('calidad', {
      'indice-calidad-historico': {
        data: [
          {
            indice_consolidado: 0.5,
            pct_completitud: 0.8,
            pct_descarte: 0.1,
            pct_fusion: 0.05,
            pct_cobertura_evidencia: 0.01,
          },
        ],
      },
      'completitud-campos-criticos': {
        data: [{ pct_completitud: 0.8, completos: 8, casos: 10, campos_comprobados: 5 }],
      },
      'campos-mas-ausentes': {
        data: [
          { campo: 'severidad', pct_ausencia: 0, ausencias: 0, casos: 10 },
          { campo: 'condado', pct_ausencia: 0.2, ausencias: 2, casos: 10 },
        ],
      },
      'calidad-por-origen': { data: [{ origen: 'central', pct_completitud: 0.9, casos: 6 }] },
    });
    expect(texto('zona-heroe')).toContain('completitud');
    expect(texto('ranking-ausencias')).toContain('severidad');
    expect(html().toLowerCase()).not.toContain('cumple');
  });

  it('vacio_no_pinta_calidad_cero', () => {
    montar('calidad');
    flushTodos('calidad', {});
    expect(texto('zona-heroe')).toContain('Sin accidentes');
    expect(texto('zona-heroe')).not.toContain('0 %');
  });

  it('concentracion_es_ranking_no_mapa', () => {
    montar('concentracion');
    flushTodos('concentracion', {
      'concentracion-siniestralidad': {
        data: [{ zona: 'Orange', casos: 40, pct: 0.4 }],
      },
      'patron-horario-climatico': {
        data: [
          {
            franja: 'noche',
            dia_semana: '6',
            casos: 10,
            casos_con_clima: 3,
            cobertura: 'parcial',
          },
        ],
      },
    });
    expect(texto('zona-heroe')).toContain('Orange');
    expect(texto('zona-visual').toLowerCase()).toContain('parcial');
    expect(html().toLowerCase()).not.toContain('leaflet');
    expect(html().toLowerCase()).not.toContain('latitud');
  });

  it('impacto_no_finge_ceros', () => {
    montar('impacto');
    flushTodos('impacto', {
      'impacto-humano-por-zona': {
        data: [
          {
            condado: 'Orange',
            severidad: 'Grave',
            victimas: 4,
            casos_con_dato: 2,
            casos: 10,
          },
        ],
      },
      'impacto-vial-por-zona': {
        data: [
          {
            condado: 'Orange',
            duracion_media: 30,
            casos_con_duracion: 8,
            distancia_media: 1.2,
            casos_con_distancia: 7,
          },
        ],
      },
    });
    expect(texto('zona-heroe')).toContain('2');
    expect(texto('zona-visual')).toContain('7');
    expect(texto('alcance-denominadores').toLowerCase()).toContain('cero');
  });

  it('cobertura_marca_sin_masa_critica', () => {
    montar('cobertura');
    flushTodos('cobertura', {
      'cobertura-del-historico': {
        data: [
          { condado: 'Orange', casos: 800, umbral_casos: 500, sin_masa_critica: 0 },
          { condado: 'Lee', casos: 40, umbral_casos: 500, sin_masa_critica: 1 },
        ],
      },
    });
    expect(texto('zona-heroe')).toContain('sin masa crítica');
    expect(texto('zona-heroe')).toContain('500');
  });

  it('ninguna_pantalla_menciona_mapa_ni_bloqueados', () => {
    for (const id of ['calidad', 'concentracion', 'impacto', 'cobertura']) {
      montar(id);
      flushTodos(id, {});
      const markup = html().toLowerCase();
      expect(markup).not.toContain('leaflet');
      expect(markup).not.toContain('precision-del-modelo');
      expect(markup).not.toContain('latencia-de-ingesta');
      http.verify();
    }
  });
});
