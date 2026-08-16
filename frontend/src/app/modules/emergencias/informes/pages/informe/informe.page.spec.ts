/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { InformeEmergenciasPage } from './informe.page';

function rutaDe(informe: string) {
  const paramMap = convertToParamMap({ informe });
  return { paramMap: of(paramMap), snapshot: { paramMap, data: {} as Record<string, unknown> } };
}

describe('InformeEmergenciasPage', () => {
  let fixture: ComponentFixture<InformeEmergenciasPage>;
  let http: HttpTestingController;

  function montar(informe: string) {
    TestBed.configureTestingModule({
      imports: [InformeEmergenciasPage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ActivatedRoute, useValue: rutaDe(informe) },
      ],
    });
    fixture = TestBed.createComponent(InformeEmergenciasPage);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  }

  function peticion(informe: string) {
    return http.expectOne((r) => r.url === `/api/v1/informes/emergencias/${informe}`);
  }

  function texto(testid: string): string | null {
    const el = fixture.nativeElement.querySelector(`[data-testid="${testid}"]`);
    return el ? (el.textContent as string).replace(/\s+/g, ' ').trim() : null;
  }

  function celdas(): HTMLElement[] {
    return Array.from(fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td'));
  }

  function envelope(data: unknown[], acotadoA?: 'zonas_contratadas' | 'todos') {
    return {
      data,
      meta: {
        pagination: { cursor: null, limit: 50, has_next: false },
        filtros: {},
        ...(acotadoA ? { acotado_a: acotadoA } : {}),
      },
    };
  }

  function caso(parcial: Record<string, unknown> = {}) {
    return {
      numero_caso: 'ACC-1',
      severidad: 'Grave',
      calle: 'Avenida Central',
      ciudad: 'San Ramón',
      condado: 'Valle Norte',
      tipo_reportado: 'Colisión',
      num_vehiculos: 2,
      num_heridos: 1,
      num_victimas: 0,
      num_fallecidos: 0,
      fecha_accidente: '2026-08-10T12:00:00Z',
      activo: false,
      hora_fin: '2026-08-11T00:00:00Z',
      duracion_minutos: 45,
      duplicado_de: null,
      ...parcial,
    };
  }

  afterEach(() => http.verify());

  // ── El tercer valor de `acotado_a` ────────────────────────────────────────

  describe('el aviso de zonas contratadas', () => {
    it('zonas_contratadas_when_llega_muestra_su_aviso_propio', () => {
      montar('casos');
      peticion('casos').flush(envelope([caso()], 'zonas_contratadas'));
      fixture.detectChanges();

      expect(texto('aviso-alcance')).toContain('zonas que tienes contratadas');
    });

    it('zonas_contratadas_when_se_muestra_NO_dice_que_los_datos_sean_tuyos', () => {
      // ⚠️ Los accidentes ocurridos en una zona contratada **no pertenecen al
      // cliente**: son hechos de terceros ocurridos donde contrató cobertura.
      // Un «tus accidentes» afirmaría algo falso sobre datos ajenos.
      montar('casos');
      peticion('casos').flush(envelope([caso()], 'zonas_contratadas'));
      fixture.detectChanges();

      const aviso = texto('aviso-alcance') ?? '';

      expect(aviso).not.toContain('tus accidentes');
      expect(aviso).not.toContain('tus registros');
    });

    it('todos_when_llega_NO_muestra_aviso', () => {
      montar('casos');
      peticion('casos').flush(envelope([caso()], 'todos'));
      fixture.detectChanges();

      expect(texto('aviso-alcance')).toBeNull();
    });

    it('lista_vacia_acotada_when_se_muestra_dice_que_puede_haberlos_en_otras', () => {
      // ⛔ Un «no hay accidentes» a secas es la ambigüedad que `acotado_a`
      // existe para evitar, y es justo cuando no hay filas cuando muerde.
      montar('casos');
      peticion('casos').flush(envelope([], 'zonas_contratadas'));
      fixture.detectChanges();

      const vacio = texto('empty-state') ?? '';

      expect(vacio).toContain('No hay casos con esos criterios.');
      expect(vacio).toContain('zonas que tienes contratadas');
      expect(vacio).toContain('otras');
    });
  });

  // ── Los tres hechos, no un estado ────────────────────────────────────────

  describe('las tres formas de quedar inactivo', () => {
    it('fusionado_when_llega_muestra_de_que_caso_es_duplicado', () => {
      montar('casos');
      peticion('casos').flush(
        envelope([caso({ activo: false, hora_fin: null, duplicado_de: 'ACC-0' })], 'todos'),
      );
      fixture.detectChanges();

      const valores = celdas().map((c) => c.textContent?.trim());

      expect(valores).toContain('ACC-0');
    });

    it('descartado_when_llega_muestra_hora_fin_y_duplicado_ausentes', () => {
      // Inactivo **sin** hora de fin ni caso origen: es una falsa alarma, y se
      // distingue de un cierre sin que la pantalla infiera nada.
      montar('casos');
      peticion('casos').flush(
        envelope([caso({ activo: false, hora_fin: null, duplicado_de: null })], 'todos'),
      );
      fixture.detectChanges();

      const cabeceras = Array.from(
        fixture.nativeElement.querySelectorAll('th') as NodeListOf<HTMLElement>,
      ).map((th) => th.textContent?.trim());
      const valores = celdas().map((c) => c.textContent?.trim());

      expect(valores[cabeceras.indexOf('Hora de fin')]).toBe('—');
      expect(valores[cabeceras.indexOf('Duplicado de')]).toBe('—');
    });

    it('hora_fin_when_llega_se_muestra_como_fecha_legible', () => {
      // El backend la normaliza a ISO; la pantalla la formatea. Antes salía
      // «1786625595899» porque el backend la devolvía verbatim.
      montar('casos');
      peticion('casos').flush(
        envelope([caso({ hora_fin: '2026-08-11T00:00:00Z' })], 'todos'),
      );
      fixture.detectChanges();

      const valores = celdas().map((c) => c.textContent?.trim()).join(' ');

      // Sin fijar el día: el navegador de las pruebas puede correr en otra zona
      // horaria, y afirmar la fecha exacta haría fallar la prueba por eso — no
      // por el formato, que es lo que aquí se comprueba.
      expect(valores).toMatch(/\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}/);
      expect(valores).not.toMatch(/17\d{11}/);
      expect(valores).not.toContain('1970');
    });

    it('caso_sin_ubicacion_when_llega_no_se_omite', () => {
      montar('casos');
      peticion('casos').flush(
        envelope([caso({ calle: null, ciudad: null, condado: null })], 'todos'),
      );
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"]').length).toBe(1);
    });
  });

  // ── Ausencias en despachos y cierres ─────────────────────────────────────

  describe('los otros listados', () => {
    it('despacho_en_transito_when_llega_muestra_horas_ausentes_no_1970', () => {
      montar('despachos');
      peticion('despachos').flush(
        envelope(
          [
            {
              numero_caso: 'ACC-1',
              unidad: 'Ambulancia 01',
              origen_despacho: 'Asignación automática',
              fecha_despacho: '2026-08-11T11:30:00Z',
              fecha_llegada: null,
              fecha_retiro: null,
              retiro_forzado: false,
              en_transito: true,
            },
          ],
          'todos',
        ),
      );
      fixture.detectChanges();

      const valores = celdas().map((c) => c.textContent?.trim());

      expect(valores[4]).toBe('—');
      expect(valores[5]).toBe('—');
      expect(valores.join(' ')).not.toContain('1970');
      expect(valores[7]).toBe('Sí');
    });

    it('calificacion_ausente_when_llega_no_se_muestra_como_cero', () => {
      montar('cierres');
      peticion('cierres').flush(
        envelope(
          [
            {
              numero_caso: 'ACC-1',
              resultado_atencion: 'Atendido',
              calificacion: null,
              observaciones_finales: null,
            },
          ],
          'todos',
        ),
      );
      fixture.detectChanges();

      expect(celdas()[2].textContent?.trim()).toBe('—');
    });

    it('calificacion_cero_real_when_llega_se_muestra_como_cero', () => {
      montar('cierres');
      peticion('cierres').flush(
        envelope(
          [
            {
              numero_caso: 'ACC-1',
              resultado_atencion: 'Atendido',
              calificacion: 0,
              observaciones_finales: 'x',
            },
          ],
          'todos',
        ),
      );
      fixture.detectChanges();

      expect(celdas()[2].textContent?.trim()).toBe('0');
    });

    it('cierres_when_se_abre_NO_ofrece_rango_de_fechas', () => {
      // Su tabla no tiene fecha propia: el backend rechaza el rango con `400`.
      montar('cierres');
      peticion('cierres').flush(envelope([], 'todos'));
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('[data-testid="filtro-desde"]')).toBeNull();
    });

    it('evidencia_when_se_abre_SI_ofrece_rango_de_fechas', () => {
      montar('evidencia-fotos');
      peticion('evidencia-fotos').flush(envelope([], 'todos'));
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('[data-testid="filtro-desde"]')).not.toBeNull();
    });

    it('evidencia_sin_conexion_when_llega_muestra_dos_horas_distintas', () => {
      // El contraste es la prueba: en línea coinciden, sin conexión difieren, y
      // solo ahí se vería un error de columna.
      montar('evidencia-fotos');
      peticion('evidencia-fotos').flush(
        envelope(
          [
            {
              numero_caso: 'ACC-1',
              autor: 'Nadia Cortés',
              url: 'https://tsi/ev/1.jpg',
              sincronizado: true,
              hora_captura: '2026-08-08T12:00:00Z',
              hora_registro: '2026-08-08T12:02:11Z',
            },
            {
              numero_caso: 'ACC-1',
              autor: 'Hugo Lemos',
              url: 'https://tsi/ev/2.jpg',
              sincronizado: true,
              hora_captura: '2026-08-10T12:00:00Z',
              hora_registro: '2026-08-10T12:00:00Z',
            },
          ],
          'todos',
        ),
      );
      fixture.detectChanges();

      const filas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"]');
      const offline = Array.from(filas[0].querySelectorAll('td')).map((c) =>
        (c as HTMLElement).textContent?.trim(),
      );
      const enLinea = Array.from(filas[1].querySelectorAll('td')).map((c) =>
        (c as HTMLElement).textContent?.trim(),
      );

      expect(offline[3]).not.toBe(offline[4]);
      expect(enLinea[3]).toBe(enLinea[4]);
    });
  });
});
