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

  configurar(ruta: string, limit = LIMIT_DEFECTO): void {
    this.ruta = ruta;
    this.limit = limit;
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
