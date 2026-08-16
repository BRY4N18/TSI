/**
 * Los cuatro listados tácticos de Red Operativa, declarados.
 *
 * ⚠️ **`flota` es el único listado de la serie que emite `meta.alcance`**, y por
 * la razón de mayor consecuencia: `dado_de_alta` significa que la unidad
 * **existe**, no que pueda acudir. Su disponibilidad operativa vive en el
 * histórico y no está aquí.
 *
 * La capa compartida pinta esa advertencia. Perderla llevaría a decidir
 * cobertura sobre unidades fuera de servicio, ocupadas o ya en camino a otro
 * accidente.
 *
 * ⛔ **Sin posición de la unidad ni contacto del proveedor.** El backend no los
 * devuelve; no son columnas que falten, son datos excluidos.
 */

import { DefinicionListado } from '../../../../shared/informes/informes-listado.types';

/**
 * ⚠️ **`En_Alerta` no es `Despublicada`.**
 *
 * Una región en alerta **sigue operando** con cobertura degradada; una
 * despublicada dejó de recibir casos. Agruparlas ocultaría exactamente la
 * ventana en la que todavía se puede actuar.
 */
export const ESTADOS_REGION = [
  'En_Validación',
  'Producción',
  'En_Alerta',
  'Despublicada',
  'Rechazada',
] as const;

/**
 * ⚠️ **Una baja forzada no es una salida ordenada.**
 *
 * La forzada ocurre con un caso en curso y obliga a reasignar; la normal es una
 * unidad que se retira sin incidencia. Contarlas juntas presentaría un incidente
 * operativo y una gestión rutinaria como lo mismo.
 */
export const TIPOS_BAJA = ['Normal', 'Forzada_con_reasignación'] as const;

function opciones(valores: readonly string[]) {
  return valores.map((valor) => ({ valor, etiqueta: valor }));
}

export const INFORMES_RED_OPERATIVA: Record<string, DefinicionListado> = {
  flota: {
    ruta: 'red-operativa/flota',
    titulo: 'Composición de flota',
    mensajeVacio: 'No hay unidades con esos criterios.',
    columnas: [
      { campo: 'placa', etiqueta: 'Placa', principal: true },
      { campo: 'nombre_unidad', etiqueta: 'Unidad' },
      { campo: 'tipo_unidad', etiqueta: 'Tipo' },
      { campo: 'capacidad', etiqueta: 'Capacidad', formato: 'numero', alineacion: 'derecha', soloEscritorio: true },
      { campo: 'proveedor', etiqueta: 'Proveedor' },
      { campo: 'condado', etiqueta: 'Condado' },
      { campo: 'estado_geografico', etiqueta: 'Estado', soloEscritorio: true },
      { campo: 'zona_cobertura', etiqueta: 'Zona de cobertura', soloEscritorio: true },
      { campo: 'tipo_propiedad', etiqueta: 'Propiedad', soloEscritorio: true },
      // ⚠️ **`dado_de_alta` significa que la unidad EXISTE**, no que esté
      // disponible. La advertencia de `meta.alcance` lo dice en pantalla; la
      // etiqueta se elige para no invitar a la lectura equivocada.
      { campo: 'dado_de_alta', etiqueta: 'Dada de alta', formato: 'booleano' },
    ],
    filtros: [
      { nombre: 'proveedor', etiqueta: 'Proveedor (id)', tipo: 'numero' },
      { nombre: 'condado', etiqueta: 'Condado (id)', tipo: 'numero' },
      { nombre: 'tipo_unidad', etiqueta: 'Tipo de unidad', tipo: 'texto' },
      {
        nombre: 'dado_de_alta',
        etiqueta: 'Dada de alta',
        tipo: 'booleano',
        ayuda: 'Existir no es estar disponible: la disponibilidad no está en este listado.',
      },
    ],
  },

  'bajas-unidad': {
    ruta: 'red-operativa/bajas-unidad',
    titulo: 'Bajas de unidad',
    admiteRango: true,
    mensajeVacio: 'No hubo bajas en este período.',
    columnas: [
      { campo: 'placa', etiqueta: 'Placa', principal: true },
      { campo: 'proveedor', etiqueta: 'Proveedor' },
      { campo: 'tipo_baja', etiqueta: 'Tipo de baja' },
      { campo: 'motivo', etiqueta: 'Motivo', soloEscritorio: true },
      { campo: 'ejecutada_por', etiqueta: 'Ejecutada por', soloEscritorio: true },
      // Ausente en las normales, y eso es correcto: solo una baja forzada tiene
      // un caso afectado.
      { campo: 'caso_afectado', etiqueta: 'Caso afectado' },
      { campo: 'fecha', etiqueta: 'Fecha', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'tipo_baja',
        etiqueta: 'Tipo de baja',
        tipo: 'enumeracion',
        opciones: opciones(TIPOS_BAJA),
        ayuda: 'Una baja forzada es un incidente operativo, no una salida ordenada.',
      },
      { nombre: 'proveedor', etiqueta: 'Proveedor (id)', tipo: 'numero' },
    ],
  },

  regiones: {
    ruta: 'red-operativa/regiones',
    titulo: 'Regiones operativas',
    mensajeVacio: 'No hay regiones con esos criterios.',
    columnas: [
      { campo: 'nombre_region', etiqueta: 'Región', principal: true },
      { campo: 'estado_region', etiqueta: 'Estado' },
      { campo: 'estado_geografico', etiqueta: 'Estado geográfico' },
      { campo: 'dias_sin_cambio', etiqueta: 'Días sin cambio', formato: 'numero', alineacion: 'derecha' },
      { campo: 'fecha_actualizacion', etiqueta: 'Último cambio', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'estado_region',
        etiqueta: 'Estado de la región',
        tipo: 'enumeracion',
        opciones: opciones(ESTADOS_REGION),
        ayuda: '«En_Alerta» sigue operando con cobertura degradada; «Despublicada» no.',
      },
      { nombre: 'detenida_mas_de_dias', etiqueta: 'Detenida más de (días)', tipo: 'numero' },
    ],
  },

  'validaciones-region': {
    ruta: 'red-operativa/validaciones-region',
    titulo: 'Validaciones de región',
    admiteRango: true,
    mensajeVacio: 'No hubo validaciones en este período.',
    columnas: [
      { campo: 'region', etiqueta: 'Región', principal: true },
      { campo: 'resultado', etiqueta: 'Resultado' },
      { campo: 'motivo', etiqueta: 'Motivo', soloEscritorio: true },
      { campo: 'ejecutada_por', etiqueta: 'Ejecutada por' },
      { campo: 'fecha', etiqueta: 'Fecha', formato: 'fecha_hora' },
    ],
    filtros: [
      { nombre: 'resultado', etiqueta: 'Resultado', tipo: 'texto' },
      { nombre: 'idregionoperativa', etiqueta: 'Región (id)', tipo: 'numero' },
    ],
  },
};

export const INFORMES_RED_OPERATIVA_IDS = Object.keys(INFORMES_RED_OPERATIVA);

/** Flota y bajas admiten roles de cuenta proveedora; regiones y validaciones no. */
export const INFORMES_FLOTA = ['flota', 'bajas-unidad'];

/** ⚠️ Solo el Tecnológico: el detalle de por qué se rechaza una región. */
export const INFORME_VALIDACIONES = 'validaciones-region';
