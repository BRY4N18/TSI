/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { InformeSoportePage } from './informe.page';

function rutaDe(informe: string) {
  const paramMap = convertToParamMap({ informe });
  return { paramMap: of(paramMap), snapshot: { paramMap, data: {} as Record<string, unknown> } };
}

describe('InformeSoportePage', () => {
  let fixture: ComponentFixture<InformeSoportePage>;
  let http: HttpTestingController;

  function montar(informe: string) {
    TestBed.configureTestingModule({
      imports: [InformeSoportePage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ActivatedRoute, useValue: rutaDe(informe) },
      ],
    });
    fixture = TestBed.createComponent(InformeSoportePage);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  }

  function peticion(informe: string) {
    return http.expectOne((r) => r.url === `/api/v1/informes/soporte-cliente/${informe}`);
  }

  function texto(testid: string): string | null {
    const el = fixture.nativeElement.querySelector(`[data-testid="${testid}"]`);
    return el ? (el.textContent as string).replace(/\s+/g, ' ').trim() : null;
  }

  function envelope(data: unknown[], acotadoA?: 'propios' | 'todos') {
    return {
      data,
      meta: {
        pagination: { cursor: null, limit: 50, has_next: false },
        filtros: {},
        ...(acotadoA ? { acotado_a: acotadoA } : {}),
      },
    };
  }

  function ticket(parcial: Record<string, unknown> = {}) {
    return {
      numero_ticket: 6701,
      cuenta: 'Transportes Ferrer S.A.',
      asunto: 'No carga el expediente',
      estado: 'Abierto',
      prioridad: 'Media',
      tipo_incidencia: 'Consulta',
      servicio: 'Portal',
      agente_asignado: 'Bruno Salas',
      situacion_compromiso: 'en curso',
      factura_vinculada: null,
      fecha_registro: '2026-08-10T12:00:00Z',
      ...parcial,
    };
  }

  afterEach(() => http.verify());

  // ── Lo que este módulo viene a cerrar ─────────────────────────────────────

  describe('el aviso de alcance', () => {
    it('acotado_a_propios_when_llega_muestra_el_aviso', () => {
      // Es la garantía que el piloto de Cuentas y Clientes no pudo validar:
      // sus ocho listados son globales y no emiten `acotado_a`.
      montar('tickets');
      peticion('tickets').flush(envelope([ticket()], 'propios'));
      fixture.detectChanges();

      expect(texto('aviso-alcance')).toContain('tus registros');
    });

    it('acotado_a_todos_when_llega_NO_muestra_aviso', () => {
      // Un cartel permanente diciendo «lo ves todo» sería ruido, y enseñaría a
      // ignorar la franja donde a veces sí hay una advertencia real.
      montar('tickets');
      peticion('tickets').flush(envelope([ticket()], 'todos'));
      fixture.detectChanges();

      expect(texto('aviso-alcance')).toBeNull();
    });

    it('lista_vacia_acotada_when_se_muestra_menciona_el_acotamiento', () => {
      // ⛔ Es cuando no hay filas cuando «no hay» y «no hay de los tuyos» se
      // leen igual. Sin esto vuelve la ambigüedad que `acotado_a` evita.
      montar('tickets');
      peticion('tickets').flush(envelope([], 'propios'));
      fixture.detectChanges();

      const vacio = texto('empty-state') ?? '';

      expect(vacio).toContain('No hay tickets con esos criterios.');
      expect(vacio).toContain('entre tus registros');
    });

    it('lista_vacia_sin_acotar_when_se_muestra_solo_da_su_mensaje', () => {
      montar('tickets');
      peticion('tickets').flush(envelope([], 'todos'));
      fixture.detectChanges();

      const vacio = texto('empty-state') ?? '';

      expect(vacio).toContain('No hay tickets con esos criterios.');
      expect(vacio).not.toContain('entre tus registros');
    });
  });

  // ── El escalado automático no se atribuye a nadie ─────────────────────────

  describe('los escalados', () => {
    function escalado(parcial: Record<string, unknown> = {}) {
      return {
        numero_ticket: 6701,
        cuenta: 'Transportes Ferrer S.A.',
        tipo_escalado: 'manual',
        estado_anterior: 'En_progreso',
        estado_nuevo: 'Escalado',
        autor: 'Bruno Salas',
        fecha: '2026-08-10T12:00:00Z',
        ...parcial,
      };
    }

    it('automatico_when_llega_se_ve_sin_autor_y_no_atribuido', () => {
      montar('escalados');
      peticion('escalados').flush(
        envelope([escalado({ tipo_escalado: 'automatico', autor: null })], 'todos'),
      );
      fixture.detectChanges();

      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');

      expect(celdas[2].textContent.trim()).toBe('automatico');
      // El supervisor que lo recibe es destinatario, no autor.
      expect(celdas[5].textContent.trim()).toBe('—');
    });

    it('manual_when_llega_muestra_a_la_persona', () => {
      montar('escalados');
      peticion('escalados').flush(envelope([escalado()], 'todos'));
      fixture.detectChanges();

      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');

      expect(celdas[5].textContent.trim()).toBe('Bruno Salas');
    });

    it('rango_when_es_escalados_si_se_pinta', () => {
      montar('escalados');
      peticion('escalados').flush(envelope([], 'todos'));
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('[data-testid="filtro-desde"]')).not.toBeNull();
    });
  });

  // ── Ausencias en tickets ──────────────────────────────────────────────────

  describe('los valores ausentes', () => {
    it('ticket_sin_agente_ni_factura_when_llega_no_se_omite', () => {
      montar('tickets');
      peticion('tickets').flush(
        envelope([ticket({ agente_asignado: null, factura_vinculada: null })], 'todos'),
      );
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"]').length).toBe(1);

      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');
      expect(celdas[7].textContent.trim()).toBe('—');
      expect(celdas[9].textContent.trim()).toBe('—');
    });

    it('sin_compromiso_when_llega_se_muestra_tal_cual', () => {
      // Es el ticket que ningún vigilante revisa: colapsarlo a «en curso» o a
      // ausencia lo volvería invisible.
      montar('tickets');
      peticion('tickets').flush(
        envelope([ticket({ situacion_compromiso: 'sin compromiso' })], 'todos'),
      );
      fixture.detectChanges();

      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');

      expect(celdas[8].textContent.trim()).toBe('sin compromiso');
    });

    it('rango_when_es_tickets_no_se_pinta', () => {
      montar('tickets');
      peticion('tickets').flush(envelope([], 'todos'));
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('[data-testid="filtro-desde"]')).toBeNull();
    });
  });
});
