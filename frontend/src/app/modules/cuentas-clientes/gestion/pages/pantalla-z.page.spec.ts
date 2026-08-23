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

function envelope(resultados: unknown[], meta: Record<string, unknown> = {}) {
  return { data: { resultados }, meta };
}

describe('PantallaZPage (Cuentas)', () => {
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
    return http.expectOne((r) => r.url.endsWith(`/cuentas/${informe}`));
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

  describe('cáscara', () => {
    it('un_error_en_una_zona_deja_las_otras_visibles', () => {
      montar('ciclo');
      flushTodos('ciclo', {
        'churn-por-cohorte': {
          data: [
            {
              cohorte_alta: '2026-01',
              pct_churn: 0.2,
              bajas: 2,
              clientes_iniciales: 10,
              motivo: 'impago',
            },
          ],
        },
        'cuentas-en-riesgo': { status: 500, data: [] },
        'usuarios-vs-tope': { data: [] },
        'antiguedad-media': { data: [] },
      });
      expect(texto('zona-heroe')).toContain('2026-01');
      expect(texto('zona-lectura')).toContain('caída');
    });
  });

  describe('Ciclo', () => {
    const ok = {
      'churn-por-cohorte': {
        data: [
          {
            cohorte_alta: '2026-01',
            pct_churn: 0.2,
            bajas: 2,
            clientes_iniciales: 10,
            motivo: 'impago',
          },
        ],
      },
      'usuarios-vs-tope': {
        data: [
          {
            idcliente: 1,
            usuarios_conocidos: 3,
            tope_plan: 10,
            pct_ocupacion: 0.3,
            pct_cobertura_pertenencia: 0.095,
          },
          {
            idcliente: 2,
            usuarios_conocidos: 1,
            tope_plan: null,
            pct_ocupacion: null,
            pct_cobertura_pertenencia: 0.095,
          },
        ],
        meta: { nota_cobertura: 'Solo el 9,5 % de los usuarios tiene organización declarada.' },
      },
      'cuentas-en-riesgo': {
        data: [
          { idcliente: 3, dias_sin_actividad: 40, sin_actividad_conocida: 0 },
          { idcliente: 4, dias_sin_actividad: null, sin_actividad_conocida: 1 },
        ],
      },
      'antiguedad-media': { data: [{ tipo_cliente: 'empresa', plan: 'Pro', dias_mediana: 200 }] },
    };

    it('churn_va_por_cohorte_de_alta_y_ocupacion_lleva_cobertura', () => {
      montar('ciclo');
      flushTodos('ciclo', ok);
      expect(texto('zona-heroe')).toContain('2026-01');
      expect(texto('heroe-cifra')).toContain('20.0 %');
      expect(texto('nota-cobertura')).toContain('9,5');
      expect(texto('ocupacion-sin-dato')).toContain('sin dato');
      expect(texto('sin-actividad-conocida')).toContain('sin actividad conocida');
      expect(texto('zona-lectura')).not.toMatch(/(^|[^0-9])0 días/);
      expect(
        fixture.nativeElement.querySelectorAll('[data-bloque-vista]').length,
      ).toBeLessThanOrEqual(8);
      expect(html().toLowerCase()).not.toContain('token');
    });

    it('vacio_when_resultados_vacios_no_pinta_cero_por_ciento', () => {
      montar('ciclo');
      flushTodos('ciclo', {});
      expect(texto('zona-heroe')).toContain('Sin datos');
      expect(texto('zona-heroe')).not.toContain('0 %');
    });
  });

  describe('Incorporación', () => {
    it('etapa_en_cero_visible_y_en_proceso_no_es_cero_dias', () => {
      montar('incorporacion');
      flushTodos('incorporacion', {
        'tiempo-onboarding': {
          data: [{ dias_mediana: 12, clientes_completados: 4, en_proceso: 3 }],
        },
        'embudo-abandono': {
          data: [
            { orden: 1, etapa: 'alta', clientes_que_llegaron: 10, pct_supera: 1 },
            { orden: 4, etapa: 'verificacion', clientes_que_llegaron: 0, pct_supera: null },
          ],
          meta: { nota_catalogo: 'Etapas del catálogo declarado.' },
        },
        'tasa-aprobacion': {
          data: [{ tipo_organizacion: 'empresa', solicitudes: 5, aprobadas: 4, pct: 0.8 }],
        },
      });
      expect(texto('heroe-cifra')).toContain('12');
      expect(texto('en-proceso')).toContain('en proceso');
      expect(texto('etapa-cero')).toContain('cero');
      expect(texto('nota-catalogo')).toContain('catálogo');
      expect(html()).not.toContain('correo');
    });
  });

  describe('Acceso', () => {
    it('un_solo_get_de_concurrencia_alimenta_heroe_visual_y_apoyo', () => {
      montar('acceso');
      flushTodos('acceso', {
        'concurrencia-sesiones': {
          data: [
            {
              fecha: '2026-08-01',
              franja: 'tarde',
              concurrencia_maxima: 8,
              sesiones_iniciadas: 20,
              duracion_mediana: 12,
              sesiones_sin_cierre: 5,
              cruza_medianoche: 1,
            },
          ],
          meta: { nota_solape: 'Una sesión que cruza medianoche cuenta en ambas franjas.' },
        },
      });
      expect(texto('heroe-cifra')).toContain('8');
      expect(texto('sesiones-iniciadas')).toContain('iniciadas');
      expect(texto('nota-solape')).toContain('medianoche');
      // ⚠️ Acceso **ya no pinta zona de lectura**: era `roles-incompatibles` y
      // se retiró. Antes esta línea comprobaba que dijera «Sin datos», que es lo
      // único que llegó a decir nunca.
      expect(
        fixture.nativeElement.querySelector('[data-testid="zona-lectura"]'),
      ).toBeNull();
      expect(html().toLowerCase()).not.toContain('leaflet');
      expect(html()).not.toContain('nombre');
    });
  });
});
