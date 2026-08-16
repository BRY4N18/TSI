/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Observable, of, throwError } from 'rxjs';

import { InformesListadoService, PeticionListado } from './informes-listado.service';
import { InformesListadoStore } from './informes-listado.store';
import { ErrorListado, ListadoEnvelope } from './informes-listado.types';

interface Fila extends Record<string, unknown> {
  numero_caso: string;
}

function envelope(
  filas: Fila[],
  cursor: string | null = null,
  acotadoA?: 'todos' | 'propios' | 'zonas_contratadas',
): ListadoEnvelope<Fila> {
  return {
    data: filas,
    meta: {
      pagination: { cursor, limit: 50, has_next: cursor !== null },
      filtros: {},
      ...(acotadoA ? { acotado_a: acotadoA } : {}),
    },
  };
}

/** Registra cada petición para poder afirmar sobre el cursor enviado. */
class ApiFalsa {
  peticiones: PeticionListado[] = [];
  respuestas: ListadoEnvelope<Fila>[] = [];
  fallo: ErrorListado | null = null;

  listar(peticion: PeticionListado): Observable<ListadoEnvelope<Fila>> {
    this.peticiones.push({ ...peticion });
    if (this.fallo) {
      return throwError(() => this.fallo);
    }
    return of(this.respuestas.shift() ?? envelope([]));
  }
}

describe('InformesListadoStore', () => {
  let api: ApiFalsa;
  let store: InformesListadoStore<Fila>;

  beforeEach(() => {
    api = new ApiFalsa();
    TestBed.configureTestingModule({
      providers: [
        InformesListadoStore,
        { provide: InformesListadoService, useValue: api },
      ],
    });
    store = TestBed.inject(InformesListadoStore) as InformesListadoStore<Fila>;
    store.configurar('emergencias/casos');
  });

  describe('la primera carga', () => {
    it('primera_pagina_when_se_carga_no_envia_cursor', () => {
      api.respuestas = [envelope([{ numero_caso: 'ACC-1' }])];

      store.aplicarFiltros({});

      expect(api.peticiones[0].cursor).toBeNull();
      expect(store.filas().length).toBe(1);
    });

    it('meta_when_llega_se_expone_para_la_pantalla', () => {
      api.respuestas = [envelope([{ numero_caso: 'ACC-1' }], null, 'zonas_contratadas')];

      store.aplicarFiltros({});

      expect(store.acotadoA()).toBe('zonas_contratadas');
    });
  });

  describe('el recorrido por paginas', () => {
    it('siguiente_when_hay_cursor_lo_envia_en_la_peticion', () => {
      api.respuestas = [
        envelope([{ numero_caso: 'ACC-1' }], 'c1'),
        envelope([{ numero_caso: 'ACC-2' }], null),
      ];

      store.aplicarFiltros({});
      store.siguiente();

      expect(api.peticiones[1].cursor).toBe('c1');
      expect(store.filas()[0].numero_caso).toBe('ACC-2');
    });

    it('siguiente_when_no_hay_cursor_no_hace_nada', () => {
      api.respuestas = [envelope([{ numero_caso: 'ACC-1' }], null)];

      store.aplicarFiltros({});
      store.siguiente();

      expect(api.peticiones.length).toBe(1);
      expect(store.hayPaginaSiguiente()).toBeFalse();
    });

    it('anterior_when_se_vuelve_repite_el_cursor_de_esa_pagina', () => {
      api.respuestas = [
        envelope([{ numero_caso: 'ACC-1' }], 'c1'),
        envelope([{ numero_caso: 'ACC-2' }], 'c2'),
        envelope([{ numero_caso: 'ACC-1' }], 'c1'),
      ];

      store.aplicarFiltros({});
      store.siguiente();
      store.anterior();

      // La pila guarda los cursores visitados: volver reenvía el de la página
      // a la que se vuelve, no el de la actual.
      expect(api.peticiones.map((p) => p.cursor)).toEqual([null, 'c1', null]);
    });

    it('anterior_when_es_la_primera_pagina_no_hace_nada', () => {
      api.respuestas = [envelope([{ numero_caso: 'ACC-1' }], 'c1')];

      store.aplicarFiltros({});
      store.anterior();

      expect(api.peticiones.length).toBe(1);
      expect(store.hayPaginaAnterior()).toBeFalse();
    });

    it('numero_de_pagina_when_se_avanza_y_retrocede_lo_refleja', () => {
      api.respuestas = [
        envelope([], 'c1'),
        envelope([], 'c2'),
        envelope([], 'c1'),
      ];

      store.aplicarFiltros({});
      expect(store.numeroDePagina()).toBe(1);

      store.siguiente();
      expect(store.numeroDePagina()).toBe(2);

      store.anterior();
      expect(store.numeroDePagina()).toBe(1);
    });
  });

  describe('cambiar de filtros', () => {
    it('filtros_nuevos_when_se_aplican_vuelven_a_la_primera_pagina', () => {
      // Los cursores visitados pertenecen a la consulta anterior: reutilizarlos
      // con otros filtros pediría continuar un recorrido que ya no existe, y la
      // respuesta sería plausible y equivocada.
      api.respuestas = [
        envelope([], 'c1'),
        envelope([], 'c2'),
        envelope([], null),
      ];

      store.aplicarFiltros({});
      store.siguiente();
      store.aplicarFiltros({ severidad: 3 });

      expect(api.peticiones[2].cursor).toBeNull();
      expect(store.numeroDePagina()).toBe(1);
    });

    it('filtros_when_se_aplican_viajan_en_la_peticion', () => {
      api.respuestas = [envelope([])];

      store.aplicarFiltros({ situacion: 'cerrado' });

      expect(api.peticiones[0].filtros).toEqual({ situacion: 'cerrado' });
    });
  });

  describe('el error', () => {
    it('error_when_llega_vacia_las_filas_y_lo_expone', () => {
      api.fallo = { tipo: 'peticion', mensaje: 'filtro inválido', reintentable: false };

      store.aplicarFiltros({});

      expect(store.filas()).toEqual([]);
      expect(store.error()?.tipo).toBe('peticion');
    });

    it('error_when_llega_no_deja_avanzar_de_pagina', () => {
      // El cursor de la siguiente pertenecía a una respuesta que no llegó:
      // conservarlo dejaría avanzar sobre datos que no se leyeron.
      api.respuestas = [envelope([], 'c1')];
      store.aplicarFiltros({});
      expect(store.hayPaginaSiguiente()).toBeTrue();

      api.fallo = { tipo: 'servidor', mensaje: 'no disponible', reintentable: true };
      store.recargar();

      expect(store.hayPaginaSiguiente()).toBeFalse();
    });

    it('vacio_when_hay_error_no_se_considera_vacio', () => {
      // Un error no es una lista vacía: son dos pantallas distintas.
      api.fallo = { tipo: 'permiso', mensaje: 'sin acceso', reintentable: false };

      store.aplicarFiltros({});

      expect(store.vacio()).toBeFalse();
    });

    it('vacio_when_no_hay_filas_ni_error_si_lo_es', () => {
      api.respuestas = [envelope([])];

      store.aplicarFiltros({});

      expect(store.vacio()).toBeTrue();
    });
  });
});
