/**
 * Estado de un listado táctico: filas, filtros, paginación y error.
 *
 * Existe para que las 32 páginas no repitan la pila de cursores ni el manejo de
 * error. `lista-accidentes` ya la resuelve a mano; esto es esa misma solución,
 * una sola vez y probada.
 *
 * ⚠️ **La navegación es siguiente/anterior, nunca por número de página.** El
 * cursor es opaco y no hay total de resultados: no se puede saltar a la página
 * 7 ni decir «120 registros». Inventar un contador obligaría a contar filas,
 * que es justo lo que la paginación keyset evita para no repetir ni perder
 * registros con ingesta continua.
 *
 * Contrato: `specs/002-tactico/contrato-informes-simples-frontend.md` §2.3.
 */

import { Injectable, computed, inject, signal } from '@angular/core';

import { InformesListadoService, LIMIT_DEFECTO } from './informes-listado.service';
import {
  AcotadoA,
  Catalogos,
  ErrorListado,
  ListadoEnvelope,
  ValoresFiltro,
} from './informes-listado.types';

@Injectable()
export class InformesListadoStore<T = Record<string, unknown>> {
  private readonly api = inject(InformesListadoService);

  private ruta = '';
  private limit = LIMIT_DEFECTO;

  /** Cursores de las páginas ya visitadas. El de la actual es el último. */
  private readonly pila = signal<(string | null)[]>([null]);

  readonly filas = signal<T[]>([]);
  readonly cargando = signal(false);
  readonly error = signal<ErrorListado | null>(null);
  readonly acotadoA = signal<AcotadoA | undefined>(undefined);
  readonly alcance = signal<string | undefined>(undefined);
  readonly filtrosAplicados = signal<Record<string, unknown>>({});
  readonly filtros = signal<ValoresFiltro>({});

  private readonly cursorSiguiente = signal<string | null>(null);

  readonly hayPaginaSiguiente = computed(() => this.cursorSiguiente() !== null);
  readonly hayPaginaAnterior = computed(() => this.pila().length > 1);
  readonly numeroDePagina = computed(() => this.pila().length);
  readonly vacio = computed(
    () => !this.cargando() && this.error() === null && this.filas().length === 0,
  );

  readonly catalogos = signal<Catalogos>({});
  readonly cargandoCatalogos = signal(false);

  configurar(ruta: string, limit = LIMIT_DEFECTO): void {
    this.ruta = ruta;
    this.limit = limit;
  }

  /**
   * Carga las opciones de los desplegables de catálogo.
   *
   * ⚠️ **Un fallo aquí no rompe el listado.** El catálogo puebla los filtros, no
   * las filas: si no llega, los desplegables se quedan en «Todos» y la pantalla
   * sigue sirviendo. Propagarlo a `error` pintaría el estado de error sobre una
   * tabla que está perfectamente cargada.
   *
   * Se deja de cargar en cualquier caso, para que el «Cargando…» no se quede fijo
   * y prometa unas opciones que ya no van a llegar.
   */
  cargarCatalogos(): void {
    this.cargandoCatalogos.set(true);
    this.api.catalogos(this.ruta).subscribe({
      next: (respuesta) => {
        this.catalogos.set(respuesta.data ?? {});
        this.cargandoCatalogos.set(false);
      },
      error: () => {
        this.catalogos.set({});
        this.cargandoCatalogos.set(false);
      },
    });
  }

  /**
   * Aplica filtros nuevos y vuelve a la primera página.
   *
   * Volver al principio no es una comodidad: los cursores ya visitados
   * pertenecen a **la consulta anterior**. Reutilizarlos con otros filtros
   * pediría al backend que continuara un recorrido que ya no existe, y la
   * respuesta sería plausible y equivocada.
   */
  aplicarFiltros(valores: ValoresFiltro): void {
    this.filtros.set({ ...valores });
    this.pila.set([null]);
    this.cargar();
  }

  siguiente(): void {
    const cursor = this.cursorSiguiente();
    if (cursor === null) {
      return;
    }
    this.pila.update((pila) => [...pila, cursor]);
    this.cargar();
  }

  anterior(): void {
    if (!this.hayPaginaAnterior()) {
      return;
    }
    this.pila.update((pila) => pila.slice(0, -1));
    this.cargar();
  }

  /** Reintenta la página actual. Solo tiene sentido si el error lo permitía. */
  recargar(): void {
    this.cargar();
  }

  private cargar(): void {
    const pila = this.pila();
    const cursor = pila[pila.length - 1];

    this.cargando.set(true);
    this.error.set(null);

    this.api
      .listar<T>({
        ruta: this.ruta,
        filtros: this.filtros(),
        cursor,
        limit: this.limit,
      })
      .subscribe({
        next: (envelope) => this.recibir(envelope),
        error: (error: ErrorListado) => {
          this.cargando.set(false);
          this.filas.set([]);
          this.error.set(error);
          // El cursor de la página siguiente pertenecía a una respuesta que no
          // llegó: conservarlo dejaría avanzar sobre datos que no se leyeron.
          this.cursorSiguiente.set(null);
        },
      });
  }

  private recibir(envelope: ListadoEnvelope<T>): void {
    this.cargando.set(false);
    this.filas.set(envelope.data ?? []);
    this.cursorSiguiente.set(envelope.meta?.pagination?.cursor ?? null);
    this.acotadoA.set(envelope.meta?.acotado_a);
    this.alcance.set(envelope.meta?.alcance);
    this.filtrosAplicados.set(envelope.meta?.filtros ?? {});
  }
}
