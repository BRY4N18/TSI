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
      { campo: 'calle', etiqueta: 'Calle', soloDetalle: true },
      { campo: 'ciudad', etiqueta: 'Ciudad' },
      { campo: 'condado', etiqueta: 'Condado', soloDetalle: true },
      { campo: 'tipo_reportado', etiqueta: 'Tipo', soloDetalle: true },
      { campo: 'num_vehiculos', etiqueta: 'Vehículos', formato: 'numero', alineacion: 'derecha', soloDetalle: true },
      { campo: 'num_heridos', etiqueta: 'Heridos', formato: 'numero', alineacion: 'derecha' },
      { campo: 'num_victimas', etiqueta: 'Víctimas', formato: 'numero', alineacion: 'derecha', soloDetalle: true },
      { campo: 'num_fallecidos', etiqueta: 'Fallecidos', formato: 'numero', alineacion: 'derecha' },
      { campo: 'fecha_accidente', etiqueta: 'Ocurrido', formato: 'fecha_hora' },
      { campo: 'situacion', etiqueta: 'Situación', formato: 'enumeracion' },
      { campo: 'hora_fin', etiqueta: 'Hora de fin', formato: 'fecha_hora', soloDetalle: true },
      { campo: 'duracion_incidente_minutos', etiqueta: 'Duración del incidente (min)', formato: 'numero', alineacion: 'derecha', soloDetalle: true },
      { campo: 'duplicado_de', etiqueta: 'Duplicado de', soloDetalle: true },
    ],
    filtros: [
      {
        nombre: 'situacion',
        etiqueta: 'Situación',
        tipo: 'enumeracion',
        opciones: opciones(SITUACIONES_CASO),
        ayuda: 'Se deriva de los tres hechos del caso, no de un estado guardado.',
      },
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
      { campo: 'fecha_llegada', etiqueta: 'Llegada', formato: 'fecha_hora', soloDetalle: true },
      { campo: 'fecha_retiro', etiqueta: 'Retiro', formato: 'fecha_hora', soloDetalle: true },
      { campo: 'retiro_forzado', etiqueta: 'Retiro forzado', formato: 'booleano', soloDetalle: true },
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
      { campo: 'hora_captura', etiqueta: 'Capturada', formato: 'fecha_hora' },
      { campo: 'hora_registro', etiqueta: 'Registrada', formato: 'fecha_hora', soloDetalle: true },
      { campo: 'url', etiqueta: 'Archivo', soloDetalle: true },
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
      { campo: 'sincronizado', etiqueta: 'Sincronizada', formato: 'booleano', soloDetalle: true },
      { campo: 'hora_captura', etiqueta: 'Capturada', formato: 'fecha_hora', soloDetalle: true },
      { campo: 'hora_registro', etiqueta: 'Registrada', formato: 'fecha_hora', soloDetalle: true },
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
    mensajeVacio: 'No hay cierres con esos criterios.',
    columnas: [
      { campo: 'numero_caso', etiqueta: 'Caso', principal: true },
      { campo: 'resultado_atencion', etiqueta: 'Resultado' },
      { campo: 'calificacion', etiqueta: 'Calificación', formato: 'numero', alineacion: 'derecha' },
      { campo: 'observaciones_finales', etiqueta: 'Observaciones', soloDetalle: true },
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
