/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { InformeRedOperativaPage } from './informe.page';

function rutaDe(informe: string) {
  const paramMap = convertToParamMap({ informe });
  return { paramMap: of(paramMap), snapshot: { paramMap, data: {} as Record<string, unknown> } };
}

describe('InformeRedOperativaPage', () => {
  let fixture: ComponentFixture<InformeRedOperativaPage>;
  let http: HttpTestingController;

  function montar(informe: string) {
    TestBed.configureTestingModule({
      imports: [InformeRedOperativaPage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ActivatedRoute, useValue: rutaDe(informe) },
      ],
    });
    fixture = TestBed.createComponent(InformeRedOperativaPage);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  }

  function peticion(informe: string) {
    return http.expectOne((r) => r.url === `/api/v1/informes/red-operativa/${informe}`);
  }

  function texto(testid: string): string | null {
    const el = fixture.nativeElement.querySelector(`[data-testid="${testid}"]`);
    return el ? (el.textContent as string).replace(/\s+/g, ' ').trim() : null;
  }

  function envelope(
    data: unknown[],
    extra: { acotado_a?: string; alcance?: string } = {},
  ) {
    return {
      data,
      meta: {
        pagination: { cursor: null, limit: 50, has_next: false },
        filtros: {},
        ...extra,
      },
    };
  }

  function unidad(parcial: Record<string, unknown> = {}) {
    return {
      placa: 'AMB-001',
      nombre_unidad: 'Ambulancia 01',
      tipo_unidad: 'Ambulancia',
      capacidad: 2,
      proveedor: 'Rescate Vial',
      condado: 'Valle Norte',
      estado_geografico: 'Centro',
      zona_cobertura: 'Norte',
      tipo_propiedad: 'Propia',
      dado_de_alta: true,
      ...parcial,
    };
  }

  afterEach(() => http.verify());

  // ── El último hueco de la capa compartida ─────────────────────────────────

  describe('la advertencia de contenido (meta.alcance)', () => {
    it('flota_when_declara_su_alcance_advierte_que_existir_no_es_estar_disponible', () => {
      // ⚠️ El caso de mayor consecuencia de la serie: `dado_de_alta` significa
      // que la unidad **existe**, no que pueda acudir. Quien lo leyera como
      // cobertura decidiría sobre unidades fuera de servicio u ocupadas.
      montar('flota');
      peticion('flota').flush(
        envelope([unidad()], { acotado_a: 'todos', alcance: 'composicion_de_flota' }),
      );
      fixture.detectChanges();

      const advertencia = texto('advertencia-contenido') ?? '';

      expect(advertencia).toContain('existen');
      expect(advertencia).toContain('disponibles');
    });

    it('flota_when_no_hay_filas_la_advertencia_SIGUE_visible', () => {
      // Advierte de una lectura equivocada del listado, no de un recorte de
      // datos: no depende de que haya filas.
      montar('flota');
      peticion('flota').flush(
        envelope([], { acotado_a: 'todos', alcance: 'composicion_de_flota' }),
      );
      fixture.detectChanges();

      expect(texto('advertencia-contenido')).not.toBeNull();
    });

    it('otros_listados_when_no_declaran_alcance_no_advierten_nada', () => {
      // Solo lo declara el listado que lo necesita: en todos sería ruido.
      montar('regiones');
      peticion('regiones').flush(envelope([], { acotado_a: 'todos' }));
      fixture.detectChanges();

      expect(texto('advertencia-contenido')).toBeNull();
    });

    it('advertencia_y_aviso_when_coinciden_son_dos_mensajes_distintos', () => {
      // Uno dice **qué describe** el listado; el otro, **a quién** pertenece lo
      // que se ve. Un proveedor acotado necesita los dos.
      montar('flota');
      peticion('flota').flush(
        envelope([unidad()], { acotado_a: 'propios', alcance: 'composicion_de_flota' }),
      );
      fixture.detectChanges();

      expect(texto('advertencia-contenido')).toContain('disponibles');
      expect(texto('aviso-alcance')).toContain('tus registros');
    });
  });

  // ── Las distinciones que el departamento no puede perder ──────────────────

  describe('las distinciones del dominio', () => {
    it('baja_normal_when_llega_muestra_el_caso_afectado_ausente', () => {
      // Solo una baja forzada tiene un caso afectado: la normal es una salida
      // ordenada, y rellenarlo sugeriría un incidente que no hubo.
      montar('bajas-unidad');
      peticion('bajas-unidad').flush(
        envelope(
          [
            {
              placa: 'AMB-001',
              proveedor: 'Rescate Vial',
              motivo: 'Fin de contrato',
              tipo_baja: 'Normal',
              ejecutada_por: 'Ana',
              caso_afectado: null,
              fecha: '2026-08-10T12:00:00Z',
            },
          ],
          { acotado_a: 'todos' },
        ),
      );
      fixture.detectChanges();

      const celdas = Array.from(
        fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td'),
      ).map((c) => (c as HTMLElement).textContent?.trim());

      expect(celdas[2]).toBe('Normal');
      expect(celdas[5]).toBe('—');
    });

    it('estados_de_region_when_se_ofrecen_distinguen_alerta_de_despublicada', () => {
      // Una región en alerta **sigue operando** con cobertura degradada.
      // Agruparlas ocultaría la ventana en la que todavía se puede actuar.
      montar('regiones');
      peticion('regiones').flush(envelope([], { acotado_a: 'todos' }));
      fixture.detectChanges();

      const opciones = Array.from(
        fixture.nativeElement.querySelectorAll(
          '[data-testid="filtro-estado_region"] option',
        ) as NodeListOf<HTMLOptionElement>,
      ).map((o) => o.textContent?.trim());

      expect(opciones).toContain('En_Alerta');
      expect(opciones).toContain('Despublicada');
    });

    it('flota_when_se_muestra_no_expone_posicion_ni_contacto', () => {
      montar('flota');
      peticion('flota').flush(envelope([unidad()], { acotado_a: 'todos' }));
      fixture.detectChanges();

      const cabeceras = Array.from(
        fixture.nativeElement.querySelectorAll('th') as NodeListOf<HTMLElement>,
      ).map((th) => th.textContent?.trim().toLowerCase());

      expect(cabeceras.some((c) => c?.includes('latitud'))).toBeFalse();
      expect(cabeceras.some((c) => c?.includes('contacto'))).toBeFalse();
    });
  });
});
