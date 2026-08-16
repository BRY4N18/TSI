/**
 * Los dos listados tácticos de Soporte al Cliente, declarados.
 *
 * Columnas, filtros y enumeraciones salen **del contrato OpenAPI del backend**
 * (`specs/002-tactico/Soporte-Cliente/informes-tacticos-simples/backend/contracts/`).
 * Una prueba los compara contra él.
 */

import { DefinicionListado } from '../../../../shared/informes/informes-listado.types';

/** Los siete estados del ticket, declarados por el contrato. */
export const ESTADOS_TICKET = [
  'Abierto',
  'Pendiente_de_clasificacion',
  'En_progreso',
  'Escalado',
  'Resuelto',
  'Cerrado',
  'Reabierto',
] as const;

/**
 * ⚠️ **Cinco situaciones de compromiso, no cuatro.**
 *
 * `cumplido` lo escribe el sistema al resolver dentro de plazo, y faltaba en la
 * spec de backend hasta que se corrigió al implementarla. Y `sin compromiso` es
 * el ticket **clasificado sin plazo asignable**: el único estado en que un
 * ticket puede quedarse indefinidamente sin que ningún proceso lo mire, así que
 * ofrecerlo como filtro es justo el propósito de la distinción.
 */
export const SITUACIONES_COMPROMISO = [
  'en curso',
  'en riesgo',
  'incumplido',
  'sin compromiso',
  'cumplido',
] as const;

/** Derivado de la **ausencia de autor**, no del tipo de acción (research D3). */
export const TIPOS_ESCALADO = ['manual', 'automatico'] as const;

function opciones(valores: readonly string[]) {
  return valores.map((valor) => ({ valor, etiqueta: valor }));
}

export const INFORMES_SOPORTE: Record<string, DefinicionListado> = {
  tickets: {
    ruta: 'soporte-cliente/tickets',
    titulo: 'Cola de tickets',
    // Estado actual: el backend rechaza `desde`/`hasta` con `400`.
    mensajeVacio: 'No hay tickets con esos criterios.',
    columnas: [
      { campo: 'numero_ticket', etiqueta: 'Ticket', principal: true },
      { campo: 'cuenta', etiqueta: 'Cuenta' },
      { campo: 'asunto', etiqueta: 'Asunto' },
      { campo: 'estado', etiqueta: 'Estado' },
      { campo: 'prioridad', etiqueta: 'Prioridad' },
      { campo: 'tipo_incidencia', etiqueta: 'Tipo', soloEscritorio: true },
      { campo: 'servicio', etiqueta: 'Servicio', soloEscritorio: true },
      // Ausente si nadie lo ha tomado. **La fila no se omite**: un ticket sin
      // agente es el que más hay que ver.
      { campo: 'agente_asignado', etiqueta: 'Agente' },
      { campo: 'situacion_compromiso', etiqueta: 'Compromiso' },
      { campo: 'factura_vinculada', etiqueta: 'Factura', soloEscritorio: true },
      { campo: 'fecha_registro', etiqueta: 'Registrado', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'estado',
        etiqueta: 'Estado',
        tipo: 'enumeracion',
        opciones: opciones(ESTADOS_TICKET),
      },
      {
        nombre: 'situacion_compromiso',
        etiqueta: 'Compromiso de tiempo',
        tipo: 'enumeracion',
        opciones: opciones(SITUACIONES_COMPROMISO),
        ayuda: '«sin compromiso» son los tickets que ningún vigilante revisa.',
      },
      { nombre: 'prioridad', etiqueta: 'Prioridad', tipo: 'texto' },
      { nombre: 'tipo_incidencia', etiqueta: 'Tipo de incidencia', tipo: 'texto' },
      { nombre: 'agente', etiqueta: 'Agente (id)', tipo: 'numero' },
      { nombre: 'con_factura', etiqueta: 'Con factura vinculada', tipo: 'booleano' },
      { nombre: 'cuenta', etiqueta: 'Cuenta (id)', tipo: 'numero' },
    ],
  },

  escalados: {
    ruta: 'soporte-cliente/escalados',
    titulo: 'Escalados',
    // ⚠️ El único de hechos del período en este departamento.
    admiteRango: true,
    mensajeVacio: 'No hubo escalados en este período.',
    columnas: [
      { campo: 'numero_ticket', etiqueta: 'Ticket', principal: true },
      { campo: 'cuenta', etiqueta: 'Cuenta' },
      { campo: 'tipo_escalado', etiqueta: 'Tipo' },
      { campo: 'estado_anterior', etiqueta: 'Estado anterior', soloEscritorio: true },
      { campo: 'estado_nuevo', etiqueta: 'Estado nuevo' },
      // ⚠️ Ausente en los automáticos, y eso es **la respuesta correcta**: no
      // hubo persona que lo decidiera. El supervisor que lo recibe es
      // destinatario, no autor — atribuírselo fue un defecto ya corregido.
      { campo: 'autor', etiqueta: 'Autor' },
      { campo: 'fecha', etiqueta: 'Fecha', formato: 'fecha_hora' },
    ],
    filtros: [
      {
        nombre: 'tipo_escalado',
        etiqueta: 'Tipo de escalado',
        tipo: 'enumeracion',
        opciones: opciones(TIPOS_ESCALADO),
      },
      { nombre: 'cuenta', etiqueta: 'Cuenta (id)', tipo: 'numero' },
    ],
  },
};

export const INFORMES_SOPORTE_IDS = Object.keys(INFORMES_SOPORTE);

/** ⚠️ El único restringido a roles de atención: un reportador no entra. */
export const INFORME_ESCALADOS = 'escalados';
