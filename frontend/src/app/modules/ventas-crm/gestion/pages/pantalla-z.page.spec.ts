/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
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

function authStub(roles: string[]) {
  return {
    isAuthenticated: () => true,
    hasRole: (rol: string) => roles.includes(rol),
  };
}

describe('PantallaZPage (Ventas y CRM)', () => {
  let fixture: ComponentFixture<PantallaZPage>;
  let http: HttpTestingController;

  function montar(id: string, roles = ['DirectorMarketing']) {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [PantallaZPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ActivatedRoute, useValue: rutaDe(id) },
        { provide: AuthApiService, useValue: authStub(roles) },
      ],
    });
    fixture = TestBed.createComponent(PantallaZPage);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  }

  function pedir(informe: string) {
    return http.expectOne((r) => r.url.endsWith(`/ventas-crm/${informe}`));
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

  function htmlSinNotas(): string {
    const nodo = (fixture.nativeElement as HTMLElement).cloneNode(true) as HTMLElement;
    nodo.querySelectorAll('[data-testid="nota-indicador"]').forEach((n) => n.remove());
    return nodo.innerHTML;
  }

  afterEach(() => {
    http?.verify();
  });

  const metaTodos = { acotado_a: 'todos' };
  const metaPropios = { acotado_a: 'propios' };

  const embudoOk: Record<string, { data: unknown[]; meta?: Record<string, unknown> }> = {
    'embudo-conversion': {
      data: [
        {
          etapa_anterior: 'Contactado',
          etapa_nueva: 'Calificado',
          transiciones: 4,
          pct_paso: 0.5,
          denominador: 8,
        },
        {
          etapa_anterior: 'Propuesta',
          etapa_nueva: 'Ganado',
          transiciones: 1,
          pct_paso: 0.25,
          denominador: 4,
        },
        {
          etapa_anterior: 'Propuesta',
          etapa_nueva: 'Perdido',
          transiciones: 1,
          pct_paso: 0.25,
          denominador: 4,
        },
      ],
      meta: metaTodos,
    },
    'permanencia-por-etapa': {
      data: [
        { etapa: 'Negociación', segundos_mediana: 400000, abiertos: 2, prospectos_medidos: 3 },
        { etapa: 'Nuevo', segundos_mediana: 3600, abiertos: 0, prospectos_medidos: 5 },
      ],
      meta: metaTodos,
    },
    'motivos-perdida': {
      data: [
        { motivo: 'sin motivo registrado', etapa_abandono: 'Propuesta', perdidos: 2, pct: 1 },
      ],
      meta: metaTodos,
    },
    'carga-por-ejecutivo': {
      data: [{ idejecutivo: 7, activos: 3, valor_pipeline: 900, conversiones: 1 }],
      meta: metaTodos,
    },
    'pipeline-ponderado': {
      data: [{ etapa: 'Propuesta', valor_ponderado: 400, peso: 0.6 }],
      meta: {
        ...metaTodos,
        filtros: { nota_pesos: 'Los pesos son una convención de este informe, no una política.' },
      },
    },
  };

  const captacionOk: Record<string, { data: unknown[]; meta?: Record<string, unknown> }> = {
    'captacion-por-canal': {
      data: [
        { canal: 'Web', prospectos: 8, pct: 0.8, denominador: 10 },
        { canal: 'Desconocido', prospectos: 2, pct: 0.2, denominador: 10 },
      ],
      meta: metaTodos,
    },
    'conversion-por-canal': {
      data: [
        { canal: 'Web', prospectos: 8, convertidos: 2, pct_conversion: 0.25, denominador: 8 },
        { canal: 'Feria', prospectos: 0, convertidos: 0, pct_conversion: null, denominador: 0 },
      ],
      meta: metaTodos,
    },
    'convertidos-por-canal': {
      data: [
        {
          canal: 'Web',
          convertidos: 2,
          prospectos: 8,
          nota_indicador: 'Parte medible del indicador. Falta la inversion por canal.',
        },
      ],
      meta: metaTodos,
    },
  };

  const nutricionOk: Record<string, { data: unknown[]; meta?: Record<string, unknown> }> = {
    'efectividad-nutricion': {
      data: [
        { grupo: 'con_demo', prospectos: 4, convertidos: 2, pct_conversion: 0.5, denominador: 4 },
        { grupo: 'sin_demo', prospectos: 6, convertidos: 1, pct_conversion: 0.1667, denominador: 6 },
      ],
      meta: metaTodos,
    },
    'intensidad-demo': {
      data: [
        { idprospecto: 99, empresa: 'Acme Salud', eventos: 12, secciones_distintas: 4 },
        { idprospecto: 100, empresa: 'Acme Salud', eventos: 3, secciones_distintas: 2 },
      ],
      meta: metaTodos,
    },
    'secciones-visitadas': {
      data: [{ seccion: 'Precios', visitas: 9 }],
      meta: metaTodos,
    },
    'latencia-reaccion': {
      data: [{ avisos: 5, con_reaccion: 2, sin_reaccion: 3, segundos_mediana: 7200 }],
      meta: metaTodos,
    },
    'reglas-disparo': {
      data: [
        {
          regla_disparada: 'demo_inactiva',
          avisos: 4,
          con_reaccion: 1,
          tasa_acierto: 0.25,
          denominador: 4,
        },
      ],
      meta: metaTodos,
    },
  };

  describe('cáscara y alcance', () => {
    it('pinta_el_patron_Z_con_alcance', () => {
      montar('embudo');
      flushTodos('embudo', embudoOk);
      expect(texto('zona-heroe')).toBeTruthy();
      expect(texto('zona-periodo')).toBeTruthy();
      expect(texto('zona-alcance')).toBeTruthy();
      expect(texto('zona-visual')).toBeTruthy();
      expect(texto('zona-lectura')).toBeTruthy();
    });

    it('error_en_una_zona_no_vacia_el_heroe', () => {
      montar('embudo');
      flushTodos('embudo', {
        ...embudoOk,
        'motivos-perdida': { data: [], status: 500 },
      });
      expect(texto('heroe-cifra')).toContain('6');
      expect(texto('zona-lectura')).toContain('caída');
    });

    it('cambiar_periodo_vuelve_a_pedir_todas_las_zonas', () => {
      montar('embudo');
      flushTodos('embudo', embudoOk);
      fixture.componentInstance.onPeriodoChange({ desde: '2026-01-01', hasta: '2026-01-31' });
      fixture.detectChanges();
      for (const informe of informesDe(PANTALLAS['embudo'])) {
        const req = pedir(informe);
        expect(req.request.params.get('desde')).toBe('2026-01-01');
        req.flush(envelope([], metaTodos));
      }
      fixture.detectChanges();
    });

    it('acotado_a_propios_when_el_rol_es_director_se_lee_del_envelope', () => {
      montar('embudo', ['DirectorMarketing']);
      flushTodos('embudo', {
        ...embudoOk,
        'embudo-conversion': { ...embudoOk['embudo-conversion'], meta: metaPropios },
      });
      expect(texto('zona-alcance')).toContain('propios');
      expect(texto('zona-alcance')).not.toContain('todos');
    });

    it('acotado_a_todos_when_el_rol_es_gerente_se_lee_del_envelope', () => {
      montar('embudo', ['GerenteVentas']);
      flushTodos('embudo', embudoOk);
      expect(texto('zona-alcance')).toContain('todos');
      expect(texto('zona-alcance')).not.toContain('propios');
    });
  });

  describe('Embudo comercial', () => {
    it('vacio_when_data_vacia_no_pinta_cero_por_ciento', () => {
      montar('embudo');
      flushTodos('embudo', {});
      expect(texto('zona-heroe')).toContain('Sin datos en este período');
      expect(texto('zona-heroe')).not.toContain('0.0 %');
      expect(texto('zona-heroe')).not.toContain('0 %');
    });

    it('abiertos_se_muestran_y_no_hay_inactivos', () => {
      montar('embudo');
      flushTodos('embudo', embudoOk);
      expect(texto('abiertos')).toContain('abiertos');
      expect(html().toLowerCase()).not.toContain('inactivos');
      expect(texto('zona-heroe')).toContain('Ganado');
      expect(texto('zona-heroe')).toContain('Perdido');
    });

    it('nota_pesos_visible_al_abrir_el_apoyo', () => {
      montar('embudo');
      flushTodos('embudo', embudoOk);
      const apoyo = fixture.nativeElement.querySelector(
        '[data-testid="zona-apoyo"]',
      ) as HTMLDetailsElement;
      expect(apoyo.open).toBeFalse();
      apoyo.open = true;
      fixture.detectChanges();
      expect(texto('nota-pesos')).toContain('convención');
    });
  });

  describe('Captación por canal', () => {
    it('desconocido_y_sin_dato_y_nota_del_indicador', () => {
      montar('captacion');
      flushTodos('captacion', captacionOk);
      expect(texto('canal-desconocido')).toContain('Desconocido');
      expect(texto('conversion-sin-dato')).toContain('sin dato');
      expect(texto('nota-indicador')).toContain('Parte medible');
    });

    it('el_template_no_contiene_cac_ni_coste', () => {
      montar('captacion');
      flushTodos('captacion', captacionOk);
      const cuerpo = htmlSinNotas().toLowerCase();
      expect(cuerpo).not.toContain('cac');
      expect(cuerpo).not.toContain('coste');
      expect(cuerpo).not.toContain('costo');
    });
  });

  describe('Nutrición del prospecto', () => {
    it('vacio_when_data_vacia_no_pinta_cero_por_ciento', () => {
      montar('nutricion');
      flushTodos('nutricion', {});
      expect(texto('zona-heroe')).toContain('Sin datos en este período');
      expect(texto('zona-heroe')).not.toContain('0.0 %');
      expect(texto('zona-heroe')).not.toContain('0 %');
    });

    it('sin_reaccion_fuera_de_mediana_y_visual_por_empresa', () => {
      montar('nutricion');
      flushTodos('nutricion', nutricionOk);
      expect(texto('sin-reaccion')).toContain('fuera de la mediana');
      expect(texto('intensidad-empresa')).toContain('Acme Salud');
      expect(texto('zona-visual')).not.toContain('99');
      expect(texto('zona-visual')).not.toContain('idprospecto');
    });

    it('vista_principal_no_pasa_de_ocho_bloques_y_reglas_en_apoyo', () => {
      montar('nutricion');
      flushTodos('nutricion', nutricionOk);
      const bloques = fixture.nativeElement.querySelectorAll('[data-bloque-vista]');
      expect(bloques.length).toBeLessThanOrEqual(8);
      const apoyo = fixture.nativeElement.querySelector(
        '[data-testid="zona-apoyo"]',
      ) as HTMLDetailsElement;
      expect(apoyo).toBeTruthy();
      expect(apoyo.open).toBeFalse();
      apoyo.open = true;
      fixture.detectChanges();
      expect(fixture.nativeElement.textContent).toContain('Reglas de disparo');
    });
  });

  describe('prohibido en las tres', () => {
    it('no_hay_mapa_exportar_ni_cta_operativa', () => {
      montar('embudo');
      flushTodos('embudo', embudoOk);
      const cuerpo = html().toLowerCase();
      expect(cuerpo).not.toContain('leaflet');
      expect(cuerpo).not.toContain('exportar');
      expect(cuerpo).not.toContain('asignar');
      expect(cuerpo).not.toContain('transicionar');
      expect(cuerpo).not.toContain('disparar');
      expect(htmlSinNotas().toLowerCase()).not.toContain('cac');
    });
  });
});
