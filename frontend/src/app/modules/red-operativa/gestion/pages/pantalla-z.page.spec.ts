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

describe('PantallaZPage (Red Operativa)', () => {
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
    return http.expectOne((r) => r.url.endsWith(`/red-operativa/${informe}`));
  }

  function flushTodos(id: string, porInforme: Record<string, { data: unknown[]; meta?: Record<string, unknown>; status?: number }>) {
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

  describe('Flota y cobertura', () => {
    const flotaOk: Record<string, { data: unknown[]; meta?: Record<string, unknown> }> = {
      'condados-cobertura-critica': {
        data: [
          {
            condado: 'Norte',
            unidades: 0,
            umbral_aplicado: 5,
            sin_alternativas: true,
            unidades_vecinas: 0,
          },
        ],
        meta: { nota_umbral: 'El umbral es una convención de este informe.' },
      },
      'unidades-por-estado': {
        data: [
          { estado: 'Activa', unidades: 10, transiciones: 20 },
          { estado: 'En Misión', unidades: 2, transiciones: 6 },
        ],
      },
      'disponibilidad-declarada': {
        data: [
          { unidad: 'ABC-123', pct_disponibilidad: 0.8 },
          { unidad: 'XYZ-999', pct_disponibilidad: null },
          { unidad: 'CERO-1', pct_disponibilidad: 0 },
        ],
      },
      'cobertura-flota-por-region': {
        data: [{ region: 'Sin región asignada', unidades: 12 }],
        meta: { nota_region: 'No existe relación región-condado en el origen.' },
      },
      'pendientes-primer-acceso': { data: [{ unidad: 'A' }] },
      'rendimiento-proveedor': { data: [{ proveedor: 'P1', intentos: 4 }] },
      'rotacion-flota': { data: [{ proveedor: 'P1', bajas: 2 }] },
      'bajas-forzadas': { data: [{ proveedor: 'P1', forzadas: 1, forzadas_con_reasignacion: 0, con_caso_en_curso: 1 }] },
    };

    it('pinta_el_patron_Z', () => {
      montar('flota');
      flushTodos('flota', flotaOk);
      expect(texto('zona-heroe')).toBeTruthy();
      expect(texto('zona-periodo')).toBeTruthy();
      expect(texto('zona-visual')).toBeTruthy();
      expect(texto('zona-lectura')).toBeTruthy();
    });

    it('vacio_when_data_vacia_no_pinta_cero_por_ciento', () => {
      montar('flota');
      flushTodos('flota', {});
      expect(texto('zona-heroe')).toContain('Sin datos en este período');
      expect(texto('zona-heroe')).not.toContain('0.0 %');
      expect(texto('zona-heroe')).not.toContain('0 %');
    });

    it('en_mision_aparece_ausente_no_es_cero_y_sin_alternativas_se_lee', () => {
      montar('flota');
      flushTodos('flota', flotaOk);
      expect(texto('estado-en-mision')).toContain('En Misión');
      expect(texto('disponibilidad-ausente')).toContain('ausente');
      expect(texto('disponibilidad-cero')).toContain('0.0 %');
      expect(texto('sin-alternativas')).toContain('sin alternativas');
      expect(texto('zona-heroe')).toContain('convención');
    });

    it('la_vista_principal_no_pasa_de_ocho_bloques_y_el_apoyo_nace_plegado', () => {
      montar('flota');
      flushTodos('flota', flotaOk);
      const bloques = fixture.nativeElement.querySelectorAll('[data-bloque-vista]');
      expect(bloques.length).toBeLessThanOrEqual(8);
      const apoyo = fixture.nativeElement.querySelector('[data-testid="zona-apoyo"]') as HTMLDetailsElement;
      expect(apoyo.open).toBeFalse();
    });

    it('error_en_una_zona_no_vacia_el_heroe', () => {
      montar('flota');
      flushTodos('flota', {
        ...flotaOk,
        'bajas-forzadas': { data: [], status: 500 },
      });
      expect(texto('heroe-cifra')).toContain('1');
      expect(texto('zona-heroe')).not.toContain('caída');
    });

    it('cambiar_el_periodo_vuelve_a_pedir_todas_las_zonas', () => {
      montar('flota');
      flushTodos('flota', flotaOk);
      fixture.componentInstance.onPeriodoChange({ desde: '2026-01-01', hasta: '2026-01-31' });
      fixture.detectChanges();
      let pedidos = 0;
      for (const informe of informesDe(PANTALLAS['flota'])) {
        const req = pedir(informe);
        expect(req.request.params.get('desde')).toBe('2026-01-01');
        req.flush(envelope([]));
        pedidos += 1;
      }
      expect(pedidos).toBe(8);
    });
  });

  describe('Mercados y retirada', () => {
    it('dias_nulos_se_leen_ausentes_y_la_convencion_es_visible', () => {
      montar('mercados');
      flushTodos('mercados', {
        'mercados-activos': {
          data: [
            { estado_ciclo_vida: 'Producción', regiones: 1, pct: 0.5 },
            { estado_ciclo_vida: 'En validación', regiones: 1, pct: 0.5 },
          ],
        },
        'tiempo-puesta-operacion': {
          data: [{ region: 'Norte', dias: null, cumple_objetivo: null, dias_objetivo: 30 }],
          meta: { nota_objetivo: 'El objetivo en días es una convención de este informe.' },
        },
        'regiones-en-riesgo': {
          data: [{ region: 'Norte', unidades: 0, umbral_aplicado: 5, unidades_faltantes: 5 }],
        },
        'casos-activos-al-despublicar': {
          data: [],
          meta: { medida_exacta_desde: '2026-08-14' },
        },
        'tiempo-perdida-a-despublicacion': {
          data: [],
          meta: { medida_exacta_desde: '2026-08-14' },
        },
      });
      expect(texto('aviso-convencion-dias')).toContain('convención');
      expect(texto('dias-ausentes')).toContain('ausente');
      expect(texto('heroe-cifra')).toContain('1');
    });

    it('despublicacion_vacia_sigue_mostrando_medida_exacta_desde', () => {
      montar('mercados');
      flushTodos('mercados', {
        'mercados-activos': { data: [{ estado_ciclo_vida: 'Producción', regiones: 2, pct: 1 }] },
        'tiempo-puesta-operacion': { data: [{ region: 'Norte', dias: 10, cumple_objetivo: true }] },
        'regiones-en-riesgo': { data: [] },
        'casos-activos-al-despublicar': {
          data: [],
          meta: { medida_exacta_desde: '2026-08-14' },
        },
        'tiempo-perdida-a-despublicacion': { data: [] },
      });
      const apoyo = fixture.nativeElement.querySelector('[data-testid="zona-apoyo"]') as HTMLDetailsElement;
      apoyo.open = true;
      fixture.detectChanges();
      expect(texto('medida-exacta-desde')).toContain('2026-08-14');
      expect(fixture.nativeElement.textContent).not.toContain('nunca pasó');
    });

    it('error_en_casos_al_despublicar_no_vacia_el_heroe', () => {
      montar('mercados');
      flushTodos('mercados', {
        'mercados-activos': { data: [{ estado_ciclo_vida: 'Producción', regiones: 2, pct: 1 }] },
        'tiempo-puesta-operacion': { data: [{ region: 'Norte', dias: 4, cumple_objetivo: true }] },
        'regiones-en-riesgo': { data: [] },
        'casos-activos-al-despublicar': { data: [], status: 500 },
        'tiempo-perdida-a-despublicacion': { data: [] },
      });
      expect(texto('heroe-cifra')).toContain('2');
    });
  });

  describe('Criterios de validación', () => {
    it('tasa_nula_es_sin_dato_y_la_lectura_nombra_intentos', () => {
      montar('validacion');
      flushTodos('validacion', {
        'tasa-aprobacion-primer-intento': {
          data: [{ periodo: '2026-08', regiones_validadas: 0, aprobadas_al_primero: 0, pct_aprobacion_primer_intento: null }],
        },
        'motivos-rechazo': { data: [] },
      });
      expect(texto('zona-heroe')).toContain('sin dato');
      expect(texto('grano-intentos').toLowerCase()).toContain('intentos');
    });

    it('vacio_when_data_vacia_no_pinta_cero_por_ciento', () => {
      montar('validacion');
      flushTodos('validacion', {});
      expect(texto('zona-heroe')).toContain('Sin datos en este período');
      expect(texto('zona-heroe')).not.toContain('0.0 %');
    });

    it('no_muestra_columna_de_validador', () => {
      montar('validacion');
      flushTodos('validacion', {
        'tasa-aprobacion-primer-intento': {
          data: [{ periodo: '2026-08', regiones_validadas: 3, aprobadas_al_primero: 1, pct_aprobacion_primer_intento: 0.3333 }],
        },
        'motivos-rechazo': { data: [{ motivo: 'Cobertura insuficiente', rechazos: 2, pct: 1 }] },
      });
      const markup = html().toLowerCase();
      expect(markup).not.toContain('validador');
      expect(markup).not.toContain('ejecutada por');
      expect(texto('grano-intentos')).toContain('intentos');
      expect(texto('heroe-cifra')).toContain('33.3 %');
    });
  });

  it('no_hay_mapa_exportar_ni_cta_operativa', () => {
    montar('flota');
    flushTodos('flota', {});
    const markup = html().toLowerCase();
    expect(markup).not.toContain('leaflet');
    expect(markup).not.toContain('exportar');
    expect(markup).not.toContain('despublicar');
    expect(markup).not.toContain('dar de alta');
    expect(markup).not.toContain('validar región');
  });
});
