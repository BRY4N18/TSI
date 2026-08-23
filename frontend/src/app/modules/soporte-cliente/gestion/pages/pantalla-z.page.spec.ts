/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { informesDe, PANTALLAS, rutaHttpDe } from '../definiciones/pantallas-gestion.definiciones';
import { PantallaZPage } from './pantalla-z.page';

function rutaDe(id: string) {
  return {
    url: of([{ path: id }]),
    snapshot: { url: [{ path: id }] },
  };
}

function envelope(
  resultados: unknown[],
  meta: Record<string, unknown> = {},
  declaraciones: { codigo?: string; mensaje?: string }[] = [],
) {
  return { data: { resultados, declaraciones }, meta };
}

function authStub(roles: string[]) {
  return {
    isAuthenticated: () => true,
    hasRole: (rol: string) => roles.includes(rol),
  };
}

describe('PantallaZPage (Soporte al Cliente)', () => {
  let fixture: ComponentFixture<PantallaZPage>;
  let http: HttpTestingController;

  function montar(id: string, roles = ['GerenteExitoCliente']) {
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
    const ruta = rutaHttpDe(informe);
    return http.expectOne((r) => r.url.endsWith(`/soporte/${ruta}`));
  }

  function flushTodos(
    id: string,
    porInforme: Record<
      string,
      {
        data: unknown[];
        meta?: Record<string, unknown>;
        declaraciones?: { codigo?: string; mensaje?: string }[];
        status?: number;
      }
    >,
  ) {
    for (const informe of informesDe(PANTALLAS[id])) {
      const req = pedir(informe);
      const cfg = porInforme[informe] ?? { data: [] };
      if (cfg.status) {
        req.flush({ detail: 'caída' }, { status: cfg.status, statusText: 'Error' });
      } else {
        req.flush(envelope(cfg.data, cfg.meta ?? {}, cfg.declaraciones ?? []));
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

  const metaTodos = { acotado_a: 'todos' };
  const metaPropios = { acotado_a: 'propios' };

  const cumplimientoOk: Record<string, { data: unknown[]; meta?: Record<string, unknown> }> = {
    'cumplimiento-sla': {
      data: [
        {
          periodo: '2026-08-01',
          tickets: 14,
          con_compromiso: 9,
          sin_compromiso: 5,
          pct_cumplimiento: 11.1,
          pct_sin_compromiso: 35.7,
          sin_compromiso_por_motivo: {
            pendiente_clasificar: 4,
            sin_compromiso: 1,
            sin_configuracion: 0,
          },
        },
      ],
      meta: metaTodos,
    },
    'cumplimiento-sla-por-plan': {
      data: [
        {
          plan: 'sin plan',
          pct_cumplimiento: 11.1,
          pct_sin_compromiso: 35.7,
          con_compromiso: 9,
        },
      ],
      meta: metaTodos,
    },
    'rendimiento-agentes': {
      data: [
        {
          id_agente: 3,
          // El servicio resuelve el nombre y lo manda junto al identificador:
          // el gerente decide sobre personas, no sobre números.
          agente: 'Lucia Vera',
          asignados: 8,
          resueltos: 2,
          reabiertos: 1,
          incumplidos: 5,
          media_resolucion_s: 7200,
          sin_resolver: 6,
        },
      ],
      meta: metaTodos,
    },
    'tickets-por-servicio': {
      data: [{ servicio: 'sin servicio', tickets: 14, incumplidos: 8 }],
      meta: metaTodos,
    },
  };

  const colaOk: Record<
    string,
    {
      data: unknown[];
      meta?: Record<string, unknown>;
      declaraciones?: { codigo?: string; mensaje?: string }[];
    }
  > = {
    'tablero-cola': {
      data: [{ clave: 'Abierto', tickets: 4, sin_agente: 1, sin_primera_respuesta: 2, incumplidos: 1 }],
      meta: metaTodos,
      declaraciones: [
        {
          codigo: 'periodo_acotado_difiere_del_tablero',
          mensaje: 'Este tablero acota por período; el tablero operativo actual devuelve toda la cola.',
        },
      ],
    },
    'evolucion-incumplimiento': {
      data: [
        { periodo: '2026-08-01', tickets: 2, incumplidos: 1, pct_sin_compromiso: 0 },
        { periodo: '2026-08-02', tickets: 0, incumplidos: 0, pct_sin_compromiso: null },
      ],
      meta: metaTodos,
    },
    'escalado-automatico': {
      data: [
        {
          tipo_incidencia: 'falla',
          prioridad: 'alta',
          tickets: 3,
          con_escalado_automatico: 2,
          con_escalado_humano: 1,
          pct_escalado_automatico: 66.7,
        },
      ],
      meta: metaTodos,
    },
  };

  const tendenciasOk: Record<
    string,
    {
      data: unknown[];
      meta?: Record<string, unknown>;
      declaraciones?: { codigo?: string; mensaje?: string }[];
    }
  > = {
    'carga-entrante-resuelta': {
      data: [
        { dia: '2026-08-01', creados: 2, resueltos: 1, neto_acumulado: 1 },
        { dia: '2026-08-02', creados: 0, resueltos: 0, neto_acumulado: 1 },
      ],
      meta: metaTodos,
    },
    'reincidencia-clientes': {
      data: [{ id_cliente: 12, tipo_cliente: 'empresa', tickets: 3, tipos_distintos: 1, reaperturas: 0 }],
      meta: metaTodos,
      declaraciones: [
        {
          codigo: 'eje_servicio_sustituido',
          mensaje: 'El eje servicio no está disponible; se agrupa por tipo de incidencia.',
        },
      ],
    },
  };

  describe('cáscara y alcance', () => {
    it('pinta_el_patron_Z_con_alcance', () => {
      montar('cumplimiento');
      flushTodos('cumplimiento', cumplimientoOk);
      expect(texto('zona-heroe')).toBeTruthy();
      expect(texto('zona-periodo')).toBeTruthy();
      expect(texto('zona-alcance')).toBeTruthy();
      expect(texto('zona-visual')).toBeTruthy();
      expect(texto('zona-lectura')).toBeTruthy();
    });

    it('error_en_una_zona_no_vacia_el_heroe', () => {
      montar('cumplimiento');
      flushTodos('cumplimiento', {
        ...cumplimientoOk,
        'rendimiento-agentes': { data: [], status: 500 },
      });
      expect(texto('heroe-cifra')).toContain('11.1');
      expect(texto('zona-lectura')).toContain('caída');
    });

    it('cambiar_periodo_vuelve_a_pedir_todas_las_zonas', () => {
      montar('cumplimiento');
      flushTodos('cumplimiento', cumplimientoOk);
      fixture.componentInstance.onPeriodoChange({ desde: '2026-01-01', hasta: '2026-01-31' });
      fixture.detectChanges();
      for (const informe of informesDe(PANTALLAS['cumplimiento'])) {
        const req = pedir(informe);
        expect(req.request.params.get('desde')).toBe('2026-01-01');
        req.flush(envelope([], metaTodos));
      }
      fixture.detectChanges();
    });

    it('acotado_a_propios_when_el_rol_es_gerente_se_lee_del_envelope', () => {
      montar('cumplimiento', ['GerenteExitoCliente']);
      flushTodos('cumplimiento', {
        ...cumplimientoOk,
        'cumplimiento-sla': { ...cumplimientoOk['cumplimiento-sla'], meta: metaPropios },
      });
      expect(texto('zona-alcance')).toContain('propios');
      expect(texto('zona-alcance')).not.toContain('todos');
    });

    it('acotado_a_todos_when_el_rol_es_agente_se_lee_del_envelope', () => {
      montar('cumplimiento', ['Soporte']);
      flushTodos('cumplimiento', cumplimientoOk);
      expect(texto('zona-alcance')).toContain('todos');
      expect(texto('zona-alcance')).not.toContain('propios');
    });
  });

  describe('Cumplimiento de SLA', () => {
    it('vacio_when_resultados_vacios_no_pinta_cero_por_ciento', () => {
      montar('cumplimiento');
      flushTodos('cumplimiento', {});
      expect(texto('zona-heroe')).toContain('Sin datos en este período');
      expect(texto('zona-heroe')).not.toContain('0.0 %');
      expect(texto('zona-heroe')).not.toContain('0 %');
    });

    it('el_par_cumplimiento_y_cobertura_viaja_en_el_mismo_bloque', () => {
      montar('cumplimiento');
      flushTodos('cumplimiento', cumplimientoOk);
      const par = texto('par-cobertura');
      expect(par).toContain('11.1');
      expect(par).toContain('35.7');
      expect(texto('heroe-cifra')).toContain('11.1');
      expect(texto('zona-lectura')).toContain('reabiertos');
      // ⚠️ Esta aserción cambió de sentido el 2026-08-22: afirmaba que la fila
      // decía «Agente 3» y **no** un nombre, que era exactamente el defecto.
      // El servicio resuelve el nombre desde el mismo repositorio que ya usaba
      // el listado simple de tickets; faltaba hacerlo aquí.
      expect(texto('fila-agente')).toContain('Lucia Vera');
      expect(texto('fila-agente')).not.toContain('Agente #');
      const bloques = fixture.nativeElement.querySelectorAll('[data-bloque-vista]');
      expect(bloques.length).toBeLessThanOrEqual(8);
    });

    it('agente_que_no_resuelve_when_llega_se_ve_como_anomalia_no_como_nombre', () => {
      // Un identificador que no resuelve significa que el agente ya no existe o
      // que la carga se adelantó. El respaldo lleva `#` a propósito: disfrazarlo
      // de nombre lo haría indistinguible de un agente normal.
      const sinNombre = JSON.parse(JSON.stringify(cumplimientoOk));
      delete sinNombre['rendimiento-agentes'].data[0].agente;

      montar('cumplimiento');
      flushTodos('cumplimiento', sinNombre);

      expect(texto('fila-agente')).toContain('Agente #3');
    });

    it('pct_nulo_es_sin_dato_y_sigue_mostrando_cobertura', () => {
      montar('cumplimiento');
      flushTodos('cumplimiento', {
        ...cumplimientoOk,
        'cumplimiento-sla': {
          data: [
            {
              periodo: '2026-08-01',
              tickets: 3,
              con_compromiso: 0,
              sin_compromiso: 3,
              pct_cumplimiento: null,
              pct_sin_compromiso: 100,
            },
          ],
          meta: metaTodos,
        },
      });
      expect(texto('heroe-sin-dato')).toContain('sin dato');
      expect(texto('par-cobertura')).toContain('sin compromiso');
    });
  });

  describe('Cola en curso', () => {
    it('agrupar_por_re_pide_solo_el_tablero', () => {
      montar('cola');
      flushTodos('cola', colaOk);
      fixture.componentInstance.onAgrupar('agente');
      fixture.detectChanges();
      const req = pedir('tablero-cola');
      expect(req.request.params.get('agrupar_por')).toBe('agente');
      req.flush(envelope(colaOk['tablero-cola'].data, metaTodos));
      fixture.detectChanges();
    });

    it('dia_con_tickets_cero_se_pinta_y_no_hay_total_escalados', () => {
      montar('cola');
      flushTodos('cola', colaOk);
      expect(texto('punto-evolucion')).toBeTruthy();
      expect(html()).toContain('2026-08-02');
      expect(texto('escalado-columnas')).toContain('automático');
      expect(texto('escalado-columnas')).toContain('humano');
      expect(html().toLowerCase()).not.toContain('total escalados');
      expect(texto('declaracion-heroe')).toContain('período');
      expect(html()).not.toContain('/soporte-cliente/dashboard');
      expect(html()).not.toContain('/soporte-cliente/tickets/');
    });
  });

  describe('Tendencias', () => {
    it('un_solo_get_de_carga_alimenta_heroe_y_visual', () => {
      montar('tendencias');
      const slugs = informesDe(PANTALLAS['tendencias']);
      expect(slugs.filter((s) => s === 'carga-entrante-resuelta').length).toBe(1);
      flushTodos('tendencias', tendenciasOk);
      expect(texto('heroe-cifra')).toContain('0');
      expect(fixture.nativeElement.querySelectorAll('[data-testid="dia-carga"]').length).toBe(2);
      expect(texto('fila-cliente')).toContain('Cliente 12');
      expect(texto('declaracion-lectura')).toContain('tipo de incidencia');
      expect(html().toLowerCase()).not.toContain('reincidencia por servicio');
      expect(fixture.nativeElement.querySelector('[data-testid="columna-servicio"]')).toBeNull();
    });

    it('vacio_when_resultados_vacios_no_pinta_cero', () => {
      montar('tendencias');
      flushTodos('tendencias', {});
      expect(texto('zona-heroe')).toContain('Sin datos en este período');
      expect(texto('zona-heroe')).not.toContain('0 %');
    });
  });

  describe('prohibido en las tres', () => {
    it('no_hay_mapa_exportar_ni_cta_operativa', () => {
      montar('cumplimiento');
      flushTodos('cumplimiento', cumplimientoOk);
      const cuerpo = html().toLowerCase();
      expect(cuerpo).not.toContain('leaflet');
      expect(cuerpo).not.toContain('exportar');
      expect(cuerpo).not.toContain('asignar');
      expect(cuerpo).not.toContain('responder');
      expect(cuerpo).not.toContain('escalar');
      expect(cuerpo).not.toContain('/soporte-cliente/tickets/');
    });
  });
});
