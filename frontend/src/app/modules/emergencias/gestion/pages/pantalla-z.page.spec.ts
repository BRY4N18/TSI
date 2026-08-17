/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

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

describe('PantallaZPage', () => {
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
    return http.expectOne((r) => r.url.endsWith(`/emergencias/${informe}`));
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

  describe('Calidad del registro', () => {
    it('pinta_el_patron_Z', () => {
      montar('calidad');
      pedir('completitud-campos-criticos').flush(
        envelope([{ periodo: '2026-08-01', casos: 10, completos: 8, pct_completitud: 0.8 }]),
      );
      fixture.detectChanges();

      expect(texto('zona-heroe')).toBeTruthy();
      expect(texto('zona-periodo')).toBeTruthy();
      expect(texto('zona-visual')).toBeTruthy();
      expect(texto('zona-lectura')).toBeTruthy();
    });

    it('vacio_when_data_vacia_no_pinta_cero_por_ciento', () => {
      montar('calidad');
      pedir('completitud-campos-criticos').flush(envelope([]));
      fixture.detectChanges();

      expect(texto('zona-heroe')).toContain('Sin datos en este período');
      expect(texto('zona-heroe')).not.toContain('0.0 %');
      expect(texto('zona-heroe')).not.toContain('0 %');
    });

    it('incompletos_when_hay_hueco_bajan_el_heroe_del_100', () => {
      montar('calidad');
      pedir('completitud-campos-criticos').flush(
        envelope([{ periodo: '2026-08-01', casos: 10, completos: 8, pct_completitud: 0.8 }]),
      );
      fixture.detectChanges();

      expect(texto('heroe-cifra')).toContain('80.0 %');
      expect(texto('heroe-cifra')).not.toContain('100');
      expect(texto('incompletos')).toContain('2');
      expect(texto('campos-comprobados')).toContain('severidad');
      expect(texto('campos-comprobados')).toContain('condado');
    });
  });

  describe('Despacho', () => {
    function flushDespacho(opts: {
      desviacion?: unknown[];
      perdidaStatus?: number;
      ratio?: unknown[];
    }) {
      pedir('primer-intento').flush(
        envelope([{ periodo: '2026-08', casos: 20, resueltos_primer_intento: 18, pct_primer_intento: 0.9 }]),
      );
      const desv = pedir('desviacion-llegada');
      desv.flush(
        envelope(
          (opts.desviacion as never) ?? [
            { unidad: 'A', desviacion_mediana: 12 },
            { unidad: 'B', desviacion_mediana: null },
          ],
          { nota_referencia: 'Valor derivado del histórico; no es un objetivo ni un SLA.' },
        ),
      );
      const perdida = pedir('perdida-senal');
      if (opts.perdidaStatus) {
        perdida.flush({ detail: 'caída' }, { status: opts.perdidaStatus, statusText: 'Error' });
      } else {
        perdida.flush(envelope([{ proveedor: 'P1', huecos: 3, intervalos_medidos: 100 }]));
      }
      pedir('ratio-demanda-capacidad').flush(
        envelope(
          (opts.ratio as never) ?? [
            { condado: 'Norte', casos: 10, unidades_vigentes: 0, ratio: null },
            { condado: 'Sur', casos: 8, unidades_vigentes: 4, ratio: 2 },
          ],
        ),
      );
      fixture.detectChanges();
    }

    it('desviacion_nula_se_lee_sin_dato_y_advierte_que_no_es_SLA', () => {
      montar('despacho');
      flushDespacho({});
      expect(texto('aviso-no-sla')).toContain('no es un objetivo ni un SLA');
      expect(texto('zona-visual')).toContain('sin dato');
    });

    it('condado_sin_unidades_se_lee_sin_capacidad', () => {
      montar('despacho');
      flushDespacho({});
      expect(texto('sin-capacidad')).toContain('sin capacidad');
      expect(fixture.nativeElement.querySelector('[data-testid="sin-capacidad"]')).toBeTruthy();
    });

    it('error_en_perdida_de_senal_no_vacia_el_heroe', () => {
      montar('despacho');
      flushDespacho({ perdidaStatus: 500 });
      expect(texto('heroe-cifra')).toContain('90.0 %');
      expect(texto('zona-lectura')).toContain('caída');
    });
  });

  describe('Evidencia y cierre', () => {
    function flushCierre() {
      pedir('envejecimiento-cartera').flush(
        envelope([{ tramo_dias: 7, casos_abiertos: 4 }]),
      );
      pedir('cobertura-evidencia').flush(
        envelope([
          {
            severidad: 'Grave',
            condado: 'Norte',
            casos: 10,
            solo_foto: 2,
            solo_nota: 1,
            foto_y_nota: 4,
            sin_evidencia: 3,
            pct_con_alguna: 0.7,
          },
        ]),
      );
      pedir('distribucion-resultados').flush(
        envelope([
          {
            resultado: 'Resuelto',
            casos: 5,
            calificados: 2,
            sin_calificar: 3,
            calificacion_media: 4.5,
          },
        ]),
      );
      pedir('retiros-forzados-por-proveedor').flush(
        envelope([{ proveedor: 'P1', retiros_forzados: 1, finalizaciones_normales: 9 }]),
      );
      pedir('latencia-sincronizacion').flush(envelope([{ pendientes: 1, sincronizadas: 4 }]));
      pedir('completitud-enriquecimiento').flush(envelope([{ pct_enriquecidos: 0.5 }]));
      pedir('volumen-evidencia-por-unidad').flush(envelope([{ evidencias: 3 }]));
      pedir('escaladas-severidad').flush(envelope([{ con_escalada: 1 }]));
      fixture.detectChanges();
    }

    it('sin_evidencia_cuenta_y_la_calificacion_ausente_no_es_cero', () => {
      montar('cierre');
      flushCierre();
      expect(texto('sin-evidencia')).toContain('3');
      expect(texto('calificacion-ausente')).toContain('ausente');
      expect(texto('calificacion-ausente')).not.toMatch(/\b0\b.*calific/);
    });

    it('la_vista_principal_no_pasa_de_ocho_bloques', () => {
      montar('cierre');
      flushCierre();
      const bloques = fixture.nativeElement.querySelectorAll('[data-bloque-vista]');
      expect(bloques.length).toBeLessThanOrEqual(8);
      const apoyo = fixture.nativeElement.querySelector('[data-testid="zona-apoyo"]') as HTMLDetailsElement;
      expect(apoyo.open).toBeFalse();
    });
  });

  it('no_hay_mapa_exportar_ni_cta_operativa', () => {
    montar('calidad');
    pedir('completitud-campos-criticos').flush(envelope([]));
    fixture.detectChanges();
    const markup = html().toLowerCase();
    expect(markup).not.toContain('leaflet');
    expect(markup).not.toContain('exportar');
    expect(markup).not.toContain('despachar');
    expect(markup).not.toContain('forzar cierre');
  });
});
