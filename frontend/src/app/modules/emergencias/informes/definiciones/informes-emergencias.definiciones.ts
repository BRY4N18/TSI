/**
 * Los cinco listados tácticos simples de Emergencias, declarados.
 *
 * ⛔ **Ninguna columna de coordenadas ni de identidad de implicados.**
 *
 * No es una omisión: el backend no las devuelve porque la constitución trata la
 * geolocalización de accidentes y la identidad de las personas implicadas como
 * dato sensible con su propio control de acceso y auditoría. **La exención de la
 * autoridad del departamento no las levanta** — es una exclusión sobre el dato,
 * no sobre quién pregunta.
 *
 * Este catálogo es el sitio donde alguien la rompería sin querer, añadiendo una
 * columna «para el mapa». Hay una prueba que lo impide.
 */

import { DefinicionListado } from '../../../../shared/informes/informes-listado.types';
import { opciones } from '../../../../shared/informes/informes-opciones';

/** Las cuatro situaciones derivadas de los tres hechos del caso. */
export const SITUACIONES_CASO = [
  'en_curso',
  'cerrado',
  'duplicado',
  'descartado',
] as const;

export const TIPOS_ESCALADO_NO_APLICA = [] as const;

export const INFORMES_EMERGENCIAS: Record<string, DefinicionListado> = {
  casos: {
    ruta: 'emergencias/casos',
    titulo: 'Casos',
    admiteRango: true,
    mensajeVacio: 'No hay casos con esos criterios.',
    columnas: [
      { campo: 'numero_caso', etiqueta: 'Caso', principal: true },
      { campo: 'severidad', etiqueta: 'Severidad' },
      // Un caso sin ubicación resoluble llega con los tres ausentes y **no se
      // omite**: es una anomalía que la supervisión necesita ver.
      { campo: 'calle', etiqueta: 'Calle', soloEscritorio: true },
      { campo: 'ciudad', etiqueta: 'Ciudad' },
      { campo: 'condado', etiqueta: 'Condado' },
      { campo: 'tipo_reportado', etiqueta: 'Tipo', soloEscritorio: true },
      { campo: 'num_vehiculos', etiqueta: 'Vehículos', formato: 'numero', alineacion: 'derecha', soloEscritorio: true },
      { campo: 'num_heridos', etiqueta: 'Heridos', formato: 'numero', alineacion: 'derecha' },
      { campo: 'num_victimas', etiqueta: 'Víctimas', formato: 'numero', alineacion: 'derecha', soloEscritorio: true },
      { campo: 'num_fallecidos', etiqueta: 'Fallecidos', formato: 'numero', alineacion: 'derecha' },
      { campo: 'fecha_accidente', etiqueta: 'Ocurrido', formato: 'fecha_hora' },
      // ── El desenlace, y los hechos de los que sale ─────────────────────────
      //
      // ⚠️ **`situacion` sustituye a la columna «Activo»**, que era el defecto:
      // cerrado, descartado y duplicado son **los tres** `activo = false`, así
      // que tres filas con «No» significaban cosas distintas — y el filtro de
      // arriba ofrecía cuatro situaciones que la tabla no sabía mostrar.
      //
      // No se deriva aquí: la calcula el backend con la misma regla que usa para
      // filtrar. Hacerlo en el último paso habría puesto una segunda copia de la
      // regla, libre de discrepar con la del filtro sin que nada fallara.
      { campo: 'situacion', etiqueta: 'Situación', formato: 'enumeracion' },
      // La columna de origen es `STRING` y guarda epoch-ms como texto, pero el
      // backend la **normaliza a ISO** antes de devolverla — como cualquier otra
      // marca de tiempo de la API. Hasta el 2026-08-15 la devolvía verbatim, y
      // en pantalla salía «1786625595899».
      { campo: 'hora_fin', etiqueta: 'Hora de fin', formato: 'fecha_hora' },
      // ⚠️ **No mide cuánto estuvo abierto el caso.** Es la duración del
      // incidente, independiente del cierre; se llamaba «Duración (min)» y, justo
      // detrás de «Hora de fin», se leía como el tiempo que el caso pasó abierto.
      { campo: 'duracion_incidente_minutos', etiqueta: 'Duración del incidente (min)', formato: 'numero', alineacion: 'derecha', soloEscritorio: true },
      { campo: 'duplicado_de', etiqueta: 'Duplicado de' },
    ],
    filtros: [
      {
        nombre: 'situacion',
        etiqueta: 'Situación',
        tipo: 'enumeracion',
        opciones: opciones(SITUACIONES_CASO),
        ayuda: 'Se deriva de los tres hechos del caso, no de un estado guardado.',
      },
      // ⚠️ Antes eran cuatro campos numéricos —«Condado (id)»— y la tabla solo
      // muestra nombres: no había forma de averiguar el número desde la propia
      // pantalla. Las opciones las sirve el backend, que además **las acota por
      // cobertura**: por eso no pueden declararse aquí como una enumeración.
      { nombre: 'severidad', etiqueta: 'Severidad', tipo: 'catalogo', catalogo: 'severidad' },
      { nombre: 'condado', etiqueta: 'Condado', tipo: 'catalogo', catalogo: 'condado' },
      { nombre: 'ciudad', etiqueta: 'Ciudad', tipo: 'catalogo', catalogo: 'ciudad' },
      { nombre: 'tipo_reportado', etiqueta: 'Tipo reportado', tipo: 'catalogo', catalogo: 'tipo_reportado' },
    ],
  },

  despachos: {
    ruta: 'emergencias/despachos',
    titulo: 'Despachos',
    admiteRango: true,
    mensajeVacio: 'No hubo despachos en este período.',
    columnas: [
      { campo: 'numero_caso', etiqueta: 'Caso', principal: true },
      { campo: 'unidad', etiqueta: 'Unidad' },
      { campo: 'origen_despacho', etiqueta: 'Origen', formato: 'enumeracion' },
      { campo: 'fecha_despacho', etiqueta: 'Despachada', formato: 'fecha_hora' },
      // ⚠️ Ausentes en una misión en tránsito, y eso es información: `0` es el
      // centinela de «aún no ha ocurrido», no la época de 1970.
      { campo: 'fecha_llegada', etiqueta: 'Llegada', formato: 'fecha_hora' },
      { campo: 'fecha_retiro', etiqueta: 'Retiro', formato: 'fecha_hora' },
      // La traza de que la central retiró a la unidad, en vez de que la unidad
      // terminara su parte.
      { campo: 'retiro_forzado', etiqueta: 'Retiro forzado', formato: 'booleano' },
      { campo: 'en_transito', etiqueta: 'En tránsito', formato: 'booleano' },
    ],
    filtros: [
      { nombre: 'en_transito', etiqueta: 'En tránsito', tipo: 'booleano' },
      { nombre: 'origen', etiqueta: 'Origen', tipo: 'catalogo', catalogo: 'origen' },
      { nombre: 'unidad', etiqueta: 'Unidad', tipo: 'catalogo', catalogo: 'unidad' },
      { nombre: 'caso', etiqueta: 'Caso', tipo: 'texto' },
    ],
  },

  'evidencia-fotos': {
    ruta: 'emergencias/evidencia-fotos',
    titulo: 'Fotografías de evidencia',
    admiteRango: true,
    mensajeVacio: 'No hay fotografías con esos criterios.',
    columnas: [
      { campo: 'numero_caso', etiqueta: 'Caso', principal: true },
      { campo: 'autor', etiqueta: 'Levantada por' },
      { campo: 'sincronizado', etiqueta: 'Sincronizada', formato: 'booleano' },
      // ⚠️ La del sitio. **Nunca se sustituye por la de subida**, que viaja
      // aparte: en una captura sin conexión difieren, y esa diferencia es
      // información.
      { campo: 'hora_captura', etiqueta: 'Capturada', formato: 'fecha_hora' },
      { campo: 'hora_registro', etiqueta: 'Registrada', formato: 'fecha_hora' },
      { campo: 'url', etiqueta: 'Archivo', soloEscritorio: true },
    ],
    filtros: [
      {
        nombre: 'sincronizado',
        etiqueta: 'Sincronizada',
        tipo: 'booleano',
        ayuda: 'La no sincronizada es evidencia que se levantó y nunca llegó.',
      },
      { nombre: 'caso', etiqueta: 'Caso', tipo: 'texto' },
      { nombre: 'autor', etiqueta: 'Autor', tipo: 'catalogo', catalogo: 'autor' },
    ],
  },

  'notas-campo': {
    ruta: 'emergencias/notas-campo',
    titulo: 'Notas de campo',
    admiteRango: true,
    mensajeVacio: 'No hay notas con esos criterios.',
    columnas: [
      { campo: 'numero_caso', etiqueta: 'Caso', principal: true },
      { campo: 'autor', etiqueta: 'Levantada por' },
      { campo: 'tipo', etiqueta: 'Tipo' },
      { campo: 'nota', etiqueta: 'Nota' },
      { campo: 'sincronizado', etiqueta: 'Sincronizada', formato: 'booleano' },
      { campo: 'hora_captura', etiqueta: 'Capturada', formato: 'fecha_hora' },
      { campo: 'hora_registro', etiqueta: 'Registrada', formato: 'fecha_hora' },
    ],
    filtros: [
      { nombre: 'sincronizado', etiqueta: 'Sincronizada', tipo: 'booleano' },
      { nombre: 'tipo', etiqueta: 'Tipo', tipo: 'texto' },
      { nombre: 'caso', etiqueta: 'Caso', tipo: 'texto' },
      { nombre: 'autor', etiqueta: 'Autor', tipo: 'catalogo', catalogo: 'autor' },
    ],
  },

  cierres: {
    ruta: 'emergencias/cierres',
    titulo: 'Cierres de caso',
    // ⚠️ **El único de estado actual.** Su tabla no tiene fecha propia —la hora
    // de fin vive en el caso—, así que el backend rechaza el rango con `400`.
    mensajeVacio: 'No hay cierres con esos criterios.',
    columnas: [
      { campo: 'numero_caso', etiqueta: 'Caso', principal: true },
      { campo: 'resultado_atencion', etiqueta: 'Resultado' },
      // ⚠️ Ausente **nunca como cero**: en una escala, cero es el peor valor, y
      // presentar «no se calificó» como la nota mínima invertiría el
      // significado. Un promedio con esos ceros hundiría la media.
      { campo: 'calificacion', etiqueta: 'Calificación', formato: 'numero', alineacion: 'derecha' },
      { campo: 'observaciones_finales', etiqueta: 'Observaciones' },
    ],
    filtros: [
      { nombre: 'resultado', etiqueta: 'Resultado', tipo: 'texto' },
      { nombre: 'sin_observaciones', etiqueta: 'Sin observaciones', tipo: 'booleano' },
      { nombre: 'con_calificacion', etiqueta: 'Con calificación', tipo: 'booleano' },
    ],
  },
};

export const INFORMES_EMERGENCIAS_IDS = Object.keys(INFORMES_EMERGENCIAS);

/** ⚠️ El único que un Cliente puede ver, y acotado a sus zonas contratadas. */
export const INFORME_CASOS = 'casos';
