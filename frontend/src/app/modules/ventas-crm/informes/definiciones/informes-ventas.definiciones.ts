/**
 * Los cuatro listados tácticos de Ventas y CRM, declarados.
 *
 * Columnas, filtros y enumeraciones salen del contrato OpenAPI del backend.
 */

import { DefinicionListado } from '../../../../shared/informes/informes-listado.types';

export const TIPOS_ORGANIZACION = ['aseguradora', 'municipio', 'proveedor'] as const;

/**
 * ⚠️ **`perdido` no es «inactivo», y `convertido` no es una pérdida.**
 *
 * Un prospecto convertido es el desenlace bueno: se volvió cliente. Agruparlo
 * con los perdidos en un recuento de «no activos» presentaría el éxito y el
 * fracaso comercial como la misma cosa.
 */
export const ESTADOS_PROSPECTO = ['activo', 'perdido', 'convertido'] as const;

export const TIPOS_ASIGNACION = ['automatica', 'manual'] as const;
export const CANALES_NOTIFICACION = ['email', 'push', 'slack'] as const;

function opciones(valores: readonly string[]) {
  return valores.map((valor) => ({ valor, etiqueta: valor }));
}

export const INFORMES_VENTAS: Record<string, DefinicionListado> = {
  prospectos: {
    ruta: 'ventas-crm/prospectos',
    titulo: 'Prospectos',
    mensajeVacio: 'No hay prospectos con esos criterios.',
    columnas: [
      { campo: 'empresa', etiqueta: 'Empresa', principal: true },
      { campo: 'nombre_contacto', etiqueta: 'Contacto' },
      { campo: 'cargo', etiqueta: 'Cargo', soloEscritorio: true },
      { campo: 'tipo_organizacion', etiqueta: 'Tipo' },
      { campo: 'canal_origen', etiqueta: 'Canal', soloEscritorio: true },
      { campo: 'etapa_actual', etiqueta: 'Etapa' },
      { campo: 'ejecutivo', etiqueta: 'Ejecutivo' },
      { campo: 'estado', etiqueta: 'Estado' },
      // Ausente salvo en los perdidos, y eso es correcto: un prospecto activo no
      // tiene motivo de pérdida que mostrar.
      { campo: 'motivo_perdida', etiqueta: 'Motivo de pérdida', soloEscritorio: true },
      { campo: 'valor_estimado', etiqueta: 'Valor estimado', formato: 'numero', alineacion: 'derecha' },
      { campo: 'fecha_registro', etiqueta: 'Registrado', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'estado',
        etiqueta: 'Estado',
        tipo: 'enumeracion',
        opciones: opciones(ESTADOS_PROSPECTO),
        ayuda: '«convertido» es el desenlace bueno, no una pérdida.',
      },
      {
        nombre: 'tipo_organizacion',
        etiqueta: 'Tipo de organización',
        tipo: 'enumeracion',
        opciones: opciones(TIPOS_ORGANIZACION),
      },
      { nombre: 'etapa', etiqueta: 'Etapa', tipo: 'texto' },
      { nombre: 'canal', etiqueta: 'Canal', tipo: 'texto' },
      { nombre: 'ejecutivo', etiqueta: 'Ejecutivo (id)', tipo: 'numero' },
    ],
  },

  reasignaciones: {
    ruta: 'ventas-crm/reasignaciones',
    titulo: 'Reasignaciones de cartera',
    admiteRango: true,
    mensajeVacio: 'No hubo reasignaciones en este período.',
    columnas: [
      { campo: 'empresa', etiqueta: 'Empresa', principal: true },
      { campo: 'ejecutivo_anterior', etiqueta: 'Ejecutivo anterior' },
      { campo: 'ejecutivo_nuevo', etiqueta: 'Ejecutivo nuevo' },
      { campo: 'tipo_asignacion', etiqueta: 'Tipo' },
      { campo: 'motivo', etiqueta: 'Motivo', soloEscritorio: true },
      { campo: 'fecha', etiqueta: 'Fecha', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'tipo_asignacion',
        etiqueta: 'Tipo de asignación',
        tipo: 'enumeracion',
        opciones: opciones(TIPOS_ASIGNACION),
      },
      { nombre: 'idprospecto', etiqueta: 'Prospecto (id)', tipo: 'numero' },
    ],
  },

  'demos-activas': {
    ruta: 'ventas-crm/demos-activas',
    titulo: 'Demos activas',
    mensajeVacio: 'No hay demos activas.',
    columnas: [
      { campo: 'empresa', etiqueta: 'Empresa', principal: true },
      { campo: 'nombre_contacto', etiqueta: 'Contacto' },
      { campo: 'ejecutivo', etiqueta: 'Ejecutivo' },
      { campo: 'expiracion', etiqueta: 'Expira', formato: 'fecha_hora' },
      { campo: 'dias_restantes', etiqueta: 'Días restantes', formato: 'numero', alineacion: 'derecha' },
    ],
    filtros: [{ nombre: 'ejecutivo', etiqueta: 'Ejecutivo (id)', tipo: 'numero' }],
  },

  'notificaciones-enviadas': {
    ruta: 'ventas-crm/notificaciones-enviadas',
    titulo: 'Notificaciones enviadas',
    admiteRango: true,
    mensajeVacio: 'No se enviaron notificaciones en este período.',
    columnas: [
      { campo: 'empresa', etiqueta: 'Empresa', principal: true },
      { campo: 'ejecutivo_notificado', etiqueta: 'Ejecutivo notificado' },
      { campo: 'regla_disparada', etiqueta: 'Regla' },
      { campo: 'canal', etiqueta: 'Canal' },
      { campo: 'fecha', etiqueta: 'Fecha', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'canal',
        etiqueta: 'Canal',
        tipo: 'enumeracion',
        opciones: opciones(CANALES_NOTIFICACION),
      },
      { nombre: 'regla', etiqueta: 'Regla', tipo: 'texto' },
      { nombre: 'ejecutivo', etiqueta: 'Ejecutivo (id)', tipo: 'numero' },
    ],
  },
};

export const INFORMES_VENTAS_IDS = Object.keys(INFORMES_VENTAS);

/**
 * ⚠️ **Supervisión pura.** El reparto de cartera es decisión de jefatura, no
 * herramienta del gerente cuya cartera se reparte: solo lo ven los roles
 * amplios.
 */
export const INFORME_REASIGNACIONES = 'reasignaciones';
