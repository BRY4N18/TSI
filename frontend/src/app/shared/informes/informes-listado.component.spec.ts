/** @marker unit */
import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InformesListadoComponent } from './informes-listado.component';
import { AcotadoA, ColumnaListado, ErrorListado } from './informes-listado.types';

interface FilaPrueba extends Record<string, unknown> {
  numero_caso: string;
  calificacion: number | null;
  hora_fin: string | null;
  activo: boolean;
}

const COLUMNAS: ColumnaListado<FilaPrueba>[] = [
  { campo: 'numero_caso', etiqueta: 'Caso', principal: true },
  { campo: 'calificacion', etiqueta: 'Calificación', formato: 'numero', alineacion: 'derecha' },
  { campo: 'hora_fin', etiqueta: 'Hora fin' },
  { campo: 'activo', etiqueta: 'Activo', formato: 'booleano' },
];

@Component({
  standalone: true,
  imports: [InformesListadoComponent],
  template: `
    <app-informes-listado
      [columnas]="columnas"
      [filas]="filas"
      [cargando]="cargando"
      [error]="error"
      [acotadoA]="acotadoA"
      [mensajeVacio]="mensajeVacio"
      [hayAnterior]="hayAnterior"
      [haySiguiente]="haySiguiente"
      [pagina]="pagina"
    />
  `,
})
class AnfitrionTest {
  columnas = COLUMNAS;
  filas: FilaPrueba[] = [];
  cargando = false;
  error: ErrorListado | null = null;
  acotadoA: AcotadoA | undefined = undefined;
  mensajeVacio = 'No hay casos registrados.';
  hayAnterior = false;
  haySiguiente = false;
  pagina = 1;
}

function texto(fixture: ComponentFixture<AnfitrionTest>, testid: string): string | null {
  const el = fixture.nativeElement.querySelector(`[data-testid="${testid}"]`);
  return el ? (el.textContent as string).replace(/\s+/g, ' ').trim() : null;
}

describe('InformesListadoComponent', () => {
  let fixture: ComponentFixture<AnfitrionTest>;
  let anfitrion: AnfitrionTest;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [AnfitrionTest] });
    fixture = TestBed.createComponent(AnfitrionTest);
    anfitrion = fixture.componentInstance;
  });

  function fila(parcial: Partial<FilaPrueba> = {}): FilaPrueba {
    return {
      numero_caso: 'ACC-1',
      calificacion: 4,
      hora_fin: '09:30',
      activo: false,
      ...parcial,
    };
  }

  describe('el valor ausente se pinta ausente, nunca como cero', () => {
    it('calificacion_when_es_null_muestra_guion_y_no_cero', () => {
      // En una escala, cero es el peor valor. Presentar «no se calificó» como
      // «se calificó con la nota mínima» invierte el significado.
      anfitrion.filas = [fila({ calificacion: null })];
      fixture.detectChanges();

      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');

      expect(celdas[1].textContent.trim()).toBe('—');
      expect(celdas[1].textContent.trim()).not.toBe('0');
    });

    it('calificacion_when_es_cero_real_muestra_cero', () => {
      // Un cero que el backend sí devolvió es un dato, no una ausencia.
      anfitrion.filas = [fila({ calificacion: 0 })];
      fixture.detectChanges();

      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');

      expect(celdas[1].textContent.trim()).toBe('0');
    });

    it('hora_fin_when_es_null_muestra_guion', () => {
      anfitrion.filas = [fila({ hora_fin: null })];
      fixture.detectChanges();

      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');

      expect(celdas[2].textContent.trim()).toBe('—');
    });
  });

  describe('el aviso de alcance', () => {
    it('acotado_a_when_es_todos_no_muestra_aviso', () => {
      // Un cartel permanente diciendo «ves todo» sería ruido, y enseñaría a
      // ignorar la franja donde a veces sí hay una advertencia real.
      anfitrion.acotadoA = 'todos';
      anfitrion.filas = [fila()];
      fixture.detectChanges();

      expect(texto(fixture, 'aviso-alcance')).toBeNull();
    });

    it('acotado_a_when_es_propios_muestra_aviso', () => {
      anfitrion.acotadoA = 'propios';
      anfitrion.filas = [fila()];
      fixture.detectChanges();

      expect(texto(fixture, 'aviso-alcance')).toContain('tus registros');
    });

    it('acotado_a_when_es_zonas_no_dice_que_los_datos_son_tuyos', () => {
      // Los accidentes de una zona contratada no pertenecen al cliente: son
      // hechos de terceros ocurridos donde contrató cobertura.
      anfitrion.acotadoA = 'zonas_contratadas';
      anfitrion.filas = [fila()];
      fixture.detectChanges();

      const aviso = texto(fixture, 'aviso-alcance') ?? '';

      expect(aviso).toContain('zonas que tienes contratadas');
      expect(aviso).not.toContain('tus accidentes');
    });

    it('lista_vacia_when_esta_acotada_lo_dice_en_el_estado_vacio', () => {
      // Es justo cuando no hay filas cuando «no hay» y «no hay de los tuyos»
      // se leen igual. Sin esto vuelve la ambigüedad que acotado_a evita.
      anfitrion.acotadoA = 'zonas_contratadas';
      anfitrion.filas = [];
      fixture.detectChanges();

      const vacio = texto(fixture, 'empty-state') ?? '';

      expect(vacio).toContain('No hay casos registrados.');
      expect(vacio).toContain('zonas que tienes contratadas');
    });

    it('lista_vacia_when_no_esta_acotada_solo_muestra_su_mensaje', () => {
      anfitrion.acotadoA = 'todos';
      anfitrion.filas = [];
      fixture.detectChanges();

      expect(texto(fixture, 'empty-state')).toContain('No hay casos registrados.');
    });
  });

  describe('un error no se convierte en tabla vacia', () => {
    it('error_400_when_llega_muestra_el_detalle_y_no_la_tabla', () => {
      anfitrion.error = {
        tipo: 'peticion',
        mensaje: "El filtro 'situacion' no admite el valor 'borrador'.",
        reintentable: false,
      };
      fixture.detectChanges();

      expect(texto(fixture, 'error-detalle')).toContain("no admite el valor 'borrador'");
      expect(texto(fixture, 'tabla-informe')).toBeNull();
      expect(texto(fixture, 'empty-state')).toBeNull();
    });

    it('error_400_when_no_es_reintentable_no_ofrece_reintentar', () => {
      anfitrion.error = { tipo: 'peticion', mensaje: 'filtro inválido', reintentable: false };
      fixture.detectChanges();

      expect(texto(fixture, 'btn-reintentar')).toBeNull();
    });

    it('error_403_when_llega_se_distingue_de_una_lista_vacia', () => {
      anfitrion.error = { tipo: 'permiso', mensaje: 'No tienes acceso.', reintentable: false };
      fixture.detectChanges();

      expect(texto(fixture, 'error-permiso')).toContain('No tienes acceso.');
      expect(texto(fixture, 'empty-state')).toBeNull();
    });

    it('error_de_servidor_when_es_reintentable_ofrece_reintentar', () => {
      anfitrion.error = { tipo: 'servidor', mensaje: 'No disponible.', reintentable: true };
      fixture.detectChanges();

      expect(texto(fixture, 'btn-reintentar')).toContain('Reintentar');
    });
  });

  describe('la paginacion', () => {
    it('paginacion_when_hay_filas_no_muestra_total_ni_numeros_de_pagina', () => {
      // El cursor es opaco y no hay recuento: inventarlo obligaría a contar
      // filas, que es lo que la paginación keyset evita.
      anfitrion.filas = [fila(), fila({ numero_caso: 'ACC-2' })];
      anfitrion.haySiguiente = true;
      fixture.detectChanges();

      const nav = texto(fixture, 'paginacion') ?? '';

      expect(nav).toContain('Página 1');
      expect(nav).not.toContain('de 2');
      expect(nav).not.toMatch(/\d+\s+registros/);
    });

    it('boton_anterior_when_es_la_primera_pagina_esta_deshabilitado', () => {
      anfitrion.filas = [fila()];
      anfitrion.hayAnterior = false;
      fixture.detectChanges();

      const boton = fixture.nativeElement.querySelector('[data-testid="btn-anterior"]');

      expect(boton.disabled).toBeTrue();
    });

    it('boton_siguiente_when_no_hay_mas_esta_deshabilitado', () => {
      anfitrion.filas = [fila()];
      anfitrion.haySiguiente = false;
      fixture.detectChanges();

      const boton = fixture.nativeElement.querySelector('[data-testid="btn-siguiente"]');

      expect(boton.disabled).toBeTrue();
    });
  });

  describe('las columnas declaradas', () => {
    it('cabeceras_when_se_declaran_cuatro_pinta_esas_cuatro', () => {
      anfitrion.filas = [fila()];
      fixture.detectChanges();

      const cabeceras = Array.from(
        fixture.nativeElement.querySelectorAll('th') as NodeListOf<HTMLElement>,
      ).map((th) => th.textContent?.trim());

      expect(cabeceras).toEqual(['Caso', 'Calificación', 'Hora fin', 'Activo']);
    });

    it('booleano_when_se_formatea_muestra_si_o_no', () => {
      anfitrion.filas = [fila({ activo: true })];
      fixture.detectChanges();

      const celdas = fixture.nativeElement.querySelectorAll('[data-testid="fila-informe"] td');

      expect(celdas[3].textContent.trim()).toBe('Sí');
    });
  });

  it('cargando_when_es_true_muestra_el_skeleton_y_no_la_tabla', () => {
    anfitrion.cargando = true;
    anfitrion.filas = [];
    fixture.detectChanges();

    expect(texto(fixture, 'loading-skeleton')).not.toBeNull();
    expect(texto(fixture, 'empty-state')).toBeNull();
  });
});
