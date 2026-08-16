/**
 * Los cuatro listados tácticos de Suscripciones y Facturación, declarados.
 *
 * ⛔ **Ningún dato del medio de cobro más allá de los últimos dígitos.** El
 * backend no devuelve el token ni el número completo: es el mismo orden de dato
 * que el secreto de un partner.
 */

import { DefinicionListado } from '../../../../shared/informes/informes-listado.types';

export const ESTADOS_SUSCRIPCION = ['Activa', 'Suspendida', 'Cancelada', 'Vencida'] as const;

/**
 * ⚠️ **`En disputa` no es una factura impaga.**
 *
 * Es una factura cuyo cobro el sistema **dejó de intentar a propósito**, porque
 * el cliente abrió una disputa. Agruparla con las fallidas llevaría a reclamar
 * un pago que la propia empresa decidió no cobrar todavía.
 */
export const ESTADOS_PAGO = ['Pendiente', 'Pagada', 'Fallida', 'En disputa'] as const;

export const ESTADOS_SOLICITUD = ['Pendiente', 'Aprobada', 'Rechazada'] as const;

function opciones(valores: readonly string[]) {
  return valores.map((valor) => ({ valor, etiqueta: valor }));
}

export const INFORMES_SUSCRIPCIONES: Record<string, DefinicionListado> = {
  suscripciones: {
    ruta: 'suscripciones-facturacion/suscripciones',
    titulo: 'Suscripciones',
    mensajeVacio: 'No hay suscripciones con esos criterios.',
    columnas: [
      { campo: 'cuenta', etiqueta: 'Cuenta', principal: true },
      { campo: 'plan', etiqueta: 'Plan' },
      { campo: 'nivel', etiqueta: 'Nivel', soloEscritorio: true },
      { campo: 'estado', etiqueta: 'Estado' },
      { campo: 'precio', etiqueta: 'Precio', formato: 'numero', alineacion: 'derecha' },
      { campo: 'periodicidad', etiqueta: 'Periodicidad', soloEscritorio: true },
      { campo: 'renovacion_automatica', etiqueta: 'Renovación automática', formato: 'booleano' },
      { campo: 'fecha_inicio', etiqueta: 'Inicio', formato: 'fecha' },
      { campo: 'fecha_fin', etiqueta: 'Fin', formato: 'fecha' },
      // Ausentes salvo en las canceladas, y eso es correcto.
      { campo: 'motivo_cancelacion', etiqueta: 'Motivo de cancelación', soloEscritorio: true },
      { campo: 'fecha_cancelacion', etiqueta: 'Cancelada', formato: 'fecha', soloEscritorio: true },
      // Objeto `{plan, se_aplica_el}`: la capa lo pinta como texto, y ausente
      // significa que no hay cambio programado.
      { campo: 'cambio_programado', etiqueta: 'Cambio programado', soloEscritorio: true },
    ],
    filtros: [
      {
        nombre: 'estado',
        etiqueta: 'Estado',
        tipo: 'enumeracion',
        opciones: opciones(ESTADOS_SUSCRIPCION),
      },
      { nombre: 'plan', etiqueta: 'Plan', tipo: 'texto' },
      { nombre: 'vence_en_dias', etiqueta: 'Vence en (días)', tipo: 'numero' },
      { nombre: 'con_cambio_programado', etiqueta: 'Con cambio programado', tipo: 'booleano' },
      { nombre: 'cuenta', etiqueta: 'Cuenta (id)', tipo: 'numero' },
    ],
  },

  facturas: {
    ruta: 'suscripciones-facturacion/facturas',
    titulo: 'Facturas',
    admiteRango: true,
    mensajeVacio: 'No hay facturas con esos criterios.',
    columnas: [
      { campo: 'numero_factura', etiqueta: 'Factura', principal: true },
      { campo: 'cuenta', etiqueta: 'Cuenta' },
      { campo: 'periodo', etiqueta: 'Período', soloEscritorio: true },
      { campo: 'tipo_documento', etiqueta: 'Tipo', soloEscritorio: true },
      { campo: 'monto_base', etiqueta: 'Base', formato: 'numero', alineacion: 'derecha', soloEscritorio: true },
      { campo: 'impuestos', etiqueta: 'Impuestos', formato: 'numero', alineacion: 'derecha', soloEscritorio: true },
      { campo: 'monto_total', etiqueta: 'Total', formato: 'numero', alineacion: 'derecha' },
      { campo: 'estado_pago', etiqueta: 'Estado de pago' },
      { campo: 'reintentos', etiqueta: 'Reintentos', formato: 'numero', alineacion: 'derecha', soloEscritorio: true },
      { campo: 'fecha_emision', etiqueta: 'Emitida', formato: 'fecha' },
      { campo: 'fecha_vencimiento', etiqueta: 'Vence', formato: 'fecha' },
      { campo: 'dias_mora', etiqueta: 'Días de mora', formato: 'numero', alineacion: 'derecha' },
    ],
    filtros: [
      {
        nombre: 'estado_pago',
        etiqueta: 'Estado de pago',
        tipo: 'enumeracion',
        opciones: opciones(ESTADOS_PAGO),
        ayuda: '«En disputa» no es impaga: el sistema dejó de cobrarla a propósito.',
      },
      { nombre: 'vencidas', etiqueta: 'Solo vencidas', tipo: 'booleano' },
      { nombre: 'cuenta', etiqueta: 'Cuenta (id)', tipo: 'numero' },
    ],
  },

  'solicitudes-cambio-plan': {
    ruta: 'suscripciones-facturacion/solicitudes-cambio-plan',
    titulo: 'Solicitudes de cambio de plan',
    mensajeVacio: 'No hay solicitudes de cambio de plan.',
    columnas: [
      { campo: 'cuenta', etiqueta: 'Cuenta', principal: true },
      { campo: 'plan_actual', etiqueta: 'Plan actual' },
      { campo: 'plan_solicitado', etiqueta: 'Plan solicitado' },
      { campo: 'estado', etiqueta: 'Estado' },
      { campo: 'motivo', etiqueta: 'Motivo', soloEscritorio: true },
      { campo: 'dias_espera', etiqueta: 'Días en espera', formato: 'numero', alineacion: 'derecha' },
      { campo: 'resuelta_por', etiqueta: 'Resuelta por', soloEscritorio: true },
      { campo: 'motivo_rechazo', etiqueta: 'Motivo de rechazo', soloEscritorio: true },
      { campo: 'fecha_solicitud', etiqueta: 'Solicitada', formato: 'fecha_hora' },
      { campo: 'fecha_resolucion', etiqueta: 'Resuelta', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'estado',
        etiqueta: 'Estado',
        tipo: 'enumeracion',
        opciones: opciones(ESTADOS_SOLICITUD),
      },
      { nombre: 'cuenta', etiqueta: 'Cuenta (id)', tipo: 'numero' },
    ],
  },

  'metodos-pago': {
    ruta: 'suscripciones-facturacion/metodos-pago',
    titulo: 'Métodos de pago',
    mensajeVacio: 'No hay métodos de pago registrados.',
    columnas: [
      { campo: 'cuenta', etiqueta: 'Cuenta', principal: true },
      { campo: 'tipo', etiqueta: 'Tipo' },
      // ⛔ Solo los últimos dígitos. El token y el número completo no salen del
      // backend: es dato de cobro, del mismo orden que el secreto de un partner.
      { campo: 'ultimos_digitos', etiqueta: 'Últimos dígitos' },
      { campo: 'fecha_expiracion', etiqueta: 'Expira', formato: 'fecha' },
      { campo: 'dias_para_caducar', etiqueta: 'Días para caducar', formato: 'numero', alineacion: 'derecha' },
    ],
    filtros: [
      { nombre: 'caduca_en_dias', etiqueta: 'Caduca en (días)', tipo: 'numero' },
      { nombre: 'cuenta', etiqueta: 'Cuenta (id)', tipo: 'numero' },
    ],
  },
};

export const INFORMES_SUSCRIPCIONES_IDS = Object.keys(INFORMES_SUSCRIPCIONES);

/** Los dos de finanzas: Director Financiero en vez de Estrategia. */
export const INFORMES_FINANZAS = ['facturas', 'metodos-pago'];
