/**
 * Tipos de los listados tácticos simples.
 *
 * Los 32 endpoints comparten envelope, paginación y forma de error, así que el
 * tipo es uno solo y las páginas solo declaran sus columnas y sus filtros.
 *
 * Contrato: `specs/002-tactico/contrato-informes-simples-frontend.md`.
 */

/** Alcance real de la respuesta, tal como lo declara `meta.acotado_a`. */
export type AcotadoA = 'todos' | 'propios' | 'zonas_contratadas';

export interface PaginacionMeta {
  /** Opaco. Se copia tal cual; **no se interpreta ni se construye a mano**. */
  cursor: string | null;
  limit: number;
  has_next: boolean;
}

export interface ListadoMeta {
  pagination: PaginacionMeta;
  /** Los filtros **aplicados y normalizados**, no los que se pidieron. */
  filtros: Record<string, unknown>;
  /**
   * Ausente en los listados que no acotan. Cuando viene, la pantalla **tiene**
   * que mostrarlo: sin él, un resultado vacío es ambiguo — «no hay» y «no hay
   * de los tuyos» se leen igual.
   */
  acotado_a?: AcotadoA;
  /** Solo lo declaran los listados cuyo nombre podría leerse como otra cosa. */
  alcance?: string;
}

export interface ListadoEnvelope<T> {
  data: T[];
  meta: ListadoMeta;
}

/** Envelope de error del backend. `detail` está escrito para leerse. */
export interface ErrorEnvelope {
  error: string;
  detail: string;
  code: string;
}

/**
 * Error de un listado, ya clasificado.
 *
 * La distinción no es cosmética: gobierna qué se le ofrece a quien lo lee.
 * Reintentar un `400` da el mismo `400`, y un `403` **no** es una lista vacía.
 */
export type TipoErrorListado = 'peticion' | 'permiso' | 'servidor' | 'red';

export interface ErrorListado {
  tipo: TipoErrorListado;
  /** El `detail` del backend cuando lo hay: nombra los valores válidos. */
  mensaje: string;
  /** `false` en `peticion` y `permiso`: repetir lo mismo devuelve lo mismo. */
  reintentable: boolean;
}

// ── Declaración de una columna ───────────────────────────────────────────────

export type FormatoColumna =
  | 'texto'
  | 'numero'
  | 'fecha'
  | 'fecha_hora'
  | 'booleano'
  /**
   * Campo de varios valores. Añadido al construir el piloto: tres listados de
   * Cuentas y Clientes devuelven arreglos (`roles`, `roles_servidor`,
   * `roles_negocio`) y sin este formato se pintaban con las comas pegadas de
   * `String(['a','b'])`.
   *
   * ⚠️ Un arreglo **vacío** es ausencia: un usuario sin roles no tiene «cero
   * roles» que mostrar, no los tiene.
   */
  | 'lista';

export interface ColumnaListado<T = Record<string, unknown>> {
  /** Clave del campo en la fila, tal como la devuelve el backend. */
  campo: keyof T & string;
  etiqueta: string;
  formato?: FormatoColumna;
  /** Destaca la columna que identifica la fila (número de caso, nombre…). */
  principal?: boolean;
  alineacion?: 'izquierda' | 'derecha';
  /** Oculta la columna en móvil, donde las filas se pintan como tarjeta. */
  soloEscritorio?: boolean;
}

// ── Declaración de un filtro ─────────────────────────────────────────────────

export type TipoFiltro = 'texto' | 'numero' | 'booleano' | 'enumeracion' | 'fecha';

export interface OpcionFiltro {
  valor: string;
  etiqueta: string;
}

export interface FiltroListado {
  /** Nombre del query param, tal como lo espera el backend. */
  nombre: string;
  etiqueta: string;
  tipo: TipoFiltro;
  /**
   * Obligatorias en `enumeracion`: pintar un desplegable con los valores
   * válidos es la mejor forma de que el `400` **no llegue a producirse**.
   */
  opciones?: OpcionFiltro[];
  ayuda?: string;
}

/**
 * Todo lo que un listado necesita declarar.
 *
 * `admiteRango` distingue los dos tipos que el backend separa: un listado de
 * **estado actual** rechaza `desde`/`hasta` con `400`, así que la barra de
 * filtros **no pinta** el selector de fechas — ofrecer un control que solo
 * sirve para provocar un error no ayuda a nadie.
 */
export interface DefinicionListado<T = Record<string, unknown>> {
  /** Ruta relativa a `/api/v1/informes/`, p. ej. `emergencias/casos`. */
  ruta: string;
  titulo: string;
  columnas: ColumnaListado<T>[];
  filtros?: FiltroListado[];
  admiteRango?: boolean;
  /** Texto del estado vacío. Debe hablar del dominio, no decir «sin datos». */
  mensajeVacio: string;
}

/** Valores de filtro tal como los mantiene la página. */
export type ValoresFiltro = Record<string, string | number | boolean | null>;
