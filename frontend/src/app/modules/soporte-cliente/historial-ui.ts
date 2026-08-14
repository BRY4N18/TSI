/**
 * Lectura humana del historial de un ticket.
 *
 * El historial se pintaba con el `tipo_accion` crudo —«escalado_automatico_sla»—
 * y con un guion en lugar del autor. Dos problemas distintos:
 *
 * 1. Un identificador interno no es una frase: quien lee el historial está
 *    reconstruyendo qué pasó con el caso de un cliente, no depurando la base.
 * 2. R-03 del SRS pide que una acción automática quede registrada
 *    **explícitamente** como del sistema, "lo que permite distinguir una decisión
 *    humana de una automática". Un guion se lee como dato que falta, no como
 *    «esto lo hizo el sistema».
 */
import { HistorialTicketItem } from './services/models/soporte.types';

const ETIQUETAS: Record<string, string> = {
  creacion: 'Ticket registrado',
  clasificacion_manual: 'Clasificado manualmente',
  asignacion: 'Ticket tomado por un agente',
  comentario: 'Comentario',
  escalado_manual: 'Escalado por un agente',
  escalado_automatico_sla: 'Escalado automáticamente por incumplimiento de SLA',
  alerta_sla_riesgo: 'Marcado en riesgo de incumplir el SLA',
  resolucion: 'Resuelto',
  cierre_confirmado: 'Cierre confirmado por el cliente',
  cierre_automatico_por_vencimiento: 'Cerrado automáticamente sin confirmación del cliente',
  reapertura: 'Reabierto por el cliente',
};

export function etiquetaAccion(tipoAccion: string): string {
  // Si aparece una acción nueva sin etiqueta, se muestra legible igualmente en
  // vez de dejar el slug crudo a la vista.
  return ETIQUETAS[tipoAccion] ?? tipoAccion.replaceAll('_', ' ');
}

/**
 * Las entradas sin `idusuario` las escribe un proceso de fondo: el vigilante de
 * SLA y el cierre automático. Decirlo es parte del requisito, no decoración.
 */
export function esAccionDelSistema(h: HistorialTicketItem): boolean {
  return h.idusuario === null || h.idusuario === undefined;
}
