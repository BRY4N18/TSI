/**
 * Los cinco listados tácticos de Partners y API, declarados.
 *
 * Columnas: contrato OpenAPI del backend.
 * Enumeraciones: las constantes que la vista valida (`domain_constants`), no el
 * typo `Produccion` que el OpenAPI tuvo hasta D6.
 */

import { DefinicionListado } from '../../../../shared/informes/informes-listado.types';

export const ESTADOS_PARTNER = [
  'Registrado',
  'Plan asignado',
  'Pruebas activo',
  'Pendiente de aprobación',
  'Producción activa',
  'Suspendido',
] as const;

export const ENTORNOS_CREDENCIAL = ['Sandbox', 'Producción'] as const;

/** Cada `CAMBIO_*` de `domain_constants`. No se agrupan. */
export const TIPOS_CAMBIO = [
  'registro',
  'asignacion_plan',
  'activacion_sandbox',
  'expiracion_sandbox',
  'solicitud_promocion_produccion',
  'activacion_produccion',
  'rechazo_promocion_produccion',
  'revocacion_credencial',
  'desactivacion_por_cascada',
  'aviso_previo_suspension',
  'suspension_automatica',
  'suspension_manual',
  'reactivacion',
] as const;

export const ESTADOS_VERSION = ['vigente', 'soportada', 'retirada'] as const;

function opciones(valores: readonly string[]) {
  return valores.map((valor) => ({ valor, etiqueta: valor }));
}

const FILTRO_PARTNER = {
  nombre: 'partner',
  etiqueta: 'Partner (id)',
  tipo: 'numero' as const,
  ayuda: 'Solo gestores. Un partner no ve este filtro.',
};

export const INFORMES_PARTNERS: Record<string, DefinicionListado> = {
  partners: {
    ruta: 'partners-api/partners',
    titulo: 'Partners',
    mensajeVacio: 'No hay partners con esos criterios.',
    columnas: [
      { campo: 'cuenta', etiqueta: 'Cuenta' },
      { campo: 'nombre_partner', etiqueta: 'Partner', principal: true },
      { campo: 'estado_acceso', etiqueta: 'Estado' },
      { campo: 'plan_api', etiqueta: 'Plan' },
      { campo: 'limite_llamadas_mes', etiqueta: 'Cupo mes', formato: 'numero', alineacion: 'derecha' },
      {
        campo: 'limite_llamadas_minuto',
        etiqueta: 'Cupo minuto',
        formato: 'numero',
        alineacion: 'derecha',
        soloEscritorio: true,
      },
      { campo: 'contacto_tecnico', etiqueta: 'Contacto', soloEscritorio: true },
      { campo: 'fecha_suspension', etiqueta: 'Suspendido', formato: 'fecha_hora', soloEscritorio: true },
      { campo: 'motivo_suspension', etiqueta: 'Motivo de suspensión' },
    ],
    filtros: [
      {
        nombre: 'estado',
        etiqueta: 'Estado',
        tipo: 'enumeracion',
        opciones: opciones(ESTADOS_PARTNER),
      },
      { nombre: 'plan', etiqueta: 'Plan', tipo: 'texto' },
      FILTRO_PARTNER,
    ],
  },

  credenciales: {
    ruta: 'partners-api/credenciales',
    titulo: 'Credenciales',
    mensajeVacio: 'No hay credenciales con esos criterios.',
    columnas: [
      { campo: 'partner', etiqueta: 'Partner' },
      { campo: 'nombre_credencial', etiqueta: 'Credencial', principal: true },
      { campo: 'entorno', etiqueta: 'Entorno' },
      { campo: 'activa', etiqueta: 'Activa', formato: 'booleano' },
      { campo: 'fecha_creacion', etiqueta: 'Creada', formato: 'fecha_hora', soloEscritorio: true },
      { campo: 'fecha_expiracion', etiqueta: 'Expira', formato: 'fecha_hora' },
      { campo: 'dias_para_caducar', etiqueta: 'Días', formato: 'numero', alineacion: 'derecha' },
    ],
    filtros: [
      {
        nombre: 'entorno',
        etiqueta: 'Entorno',
        tipo: 'enumeracion',
        opciones: opciones(ENTORNOS_CREDENCIAL),
      },
      { nombre: 'activa', etiqueta: 'Activa', tipo: 'booleano' },
      { nombre: 'caduca_en_dias', etiqueta: 'Caduca en (días)', tipo: 'numero' },
      FILTRO_PARTNER,
    ],
  },

  'cambios-acceso': {
    ruta: 'partners-api/cambios-acceso',
    titulo: 'Cambios de acceso',
    admiteRango: true,
    mensajeVacio: 'No hay cambios de acceso en este período.',
    columnas: [
      { campo: 'partner', etiqueta: 'Partner' },
      { campo: 'credencial', etiqueta: 'Credencial', soloEscritorio: true },
      { campo: 'tipo_cambio', etiqueta: 'Tipo', principal: true },
      { campo: 'estado_anterior', etiqueta: 'De', soloEscritorio: true },
      { campo: 'estado_nuevo', etiqueta: 'A' },
      { campo: 'motivo', etiqueta: 'Motivo' },
      { campo: 'ejecutado_por', etiqueta: 'Ejecutor' },
      { campo: 'fecha', etiqueta: 'Fecha', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'tipo_cambio',
        etiqueta: 'Tipo de cambio',
        tipo: 'enumeracion',
        opciones: opciones(TIPOS_CAMBIO),
        ayuda: 'Revocación y desactivación por cascada son tipos distintos.',
      },
      FILTRO_PARTNER,
    ],
  },

  'versiones-contrato': {
    ruta: 'partners-api/versiones-contrato',
    titulo: 'Versiones del contrato',
    mensajeVacio: 'No hay versiones de contrato con esos criterios.',
    columnas: [
      { campo: 'servicio', etiqueta: 'Servicio' },
      { campo: 'version', etiqueta: 'Versión', principal: true },
      { campo: 'estado', etiqueta: 'Estado' },
      { campo: 'spec_url', etiqueta: 'Spec', soloEscritorio: true },
      { campo: 'fecha_publicacion', etiqueta: 'Publicada', formato: 'fecha_hora' },
      { campo: 'fecha_retiro', etiqueta: 'Retirada', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'estado',
        etiqueta: 'Estado',
        tipo: 'enumeracion',
        opciones: opciones(ESTADOS_VERSION),
      },
      { nombre: 'servicio', etiqueta: 'Servicio (id)', tipo: 'numero' },
    ],
  },

  'alcance-datos': {
    ruta: 'partners-api/alcance-datos',
    titulo: 'Alcance de datos',
    mensajeVacio: 'No hay alcances de datos con esos criterios.',
    columnas: [
      { campo: 'cuenta', etiqueta: 'Cuenta', principal: true },
      { campo: 'zonas_geograficas', etiqueta: 'Zonas', formato: 'lista' },
      { campo: 'frecuencia_reportes', etiqueta: 'Frecuencia' },
      { campo: 'formato_reportes', etiqueta: 'Formato' },
      { campo: 'canales_notificacion', etiqueta: 'Canales', formato: 'lista', soloEscritorio: true },
      {
        campo: 'destinatarios_reportes',
        etiqueta: 'Destinatarios',
        formato: 'lista',
        soloEscritorio: true,
      },
    ],
    filtros: [
      { nombre: 'cuenta', etiqueta: 'Cuenta (id)', tipo: 'numero' },
      { nombre: 'frecuencia', etiqueta: 'Frecuencia', tipo: 'texto' },
    ],
  },
};

export const INFORMES_PARTNERS_IDS = Object.keys(INFORMES_PARTNERS);

/** Restringidos a gestores de informe. El Partner no los ve ni en el índice. */
export const INFORMES_CONTRATO = ['versiones-contrato', 'alcance-datos'] as const;
