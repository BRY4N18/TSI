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

/** Las cuatro situaciones derivadas de los tres hechos del caso. */
export const SITUACIONES_CASO = [
  'en_curso',
  'cerrado',
  'duplicado',
  'descartado',
] as const;

export const TIPOS_ESCALADO_NO_APLICA = [] as const;

function opciones(valores: readonly string[]) {
  return valores.map((valor) => ({ valor, etiqueta: valor }));
}

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
      // ── Los tres hechos, por separado ──────────────────────────────────────
      //
      // ⚠️ **No hay columna «estado».** El backend devuelve los hechos y no un
      // estado calculado, porque la exclusividad entre cerrado, descartado y
      // fusionado la garantiza el módulo de fusión, no este. Derivar la etiqueta
      // aquí repetiría en el último paso la inferencia que el backend evitó.
      { campo: 'activo', etiqueta: 'Activo', formato: 'booleano' },
      // La columna de origen es `STRING` y guarda epoch-ms como texto, pero el
      // backend la **normaliza a ISO** antes de devolverla — como cualquier otra
      // marca de tiempo de la API. Hasta el 2026-08-15 la devolvía verbatim, y
      // en pantalla salía «1786625595899».
      { campo: 'hora_fin', etiqueta: 'Hora de fin', formato: 'fecha_hora' },
      { campo: 'duracion_minutos', etiqueta: 'Duración (min)', formato: 'numero', alineacion: 'derecha', soloEscritorio: true },
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
      { nombre: 'severidad', etiqueta: 'Severidad (id)', tipo: 'numero' },
      { nombre: 'condado', etiqueta: 'Condado (id)', tipo: 'numero' },
      { nombre: 'ciudad', etiqueta: 'Ciudad (id)', tipo: 'numero' },
      { nombre: 'tipo_reportado', etiqueta: 'Tipo reportado (id)', tipo: 'numero' },
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
      { campo: 'origen_despacho', etiqueta: 'Origen' },
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
      { nombre: 'origen', etiqueta: 'Origen (id)', tipo: 'numero' },
      { nombre: 'unidad', etiqueta: 'Unidad (id)', tipo: 'numero' },
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
      { nombre: 'autor', etiqueta: 'Autor (id)', tipo: 'numero' },
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
      { nombre: 'autor', etiqueta: 'Autor (id)', tipo: 'numero' },
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
