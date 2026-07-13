import { EstadoDespacho, EstadoNotificacion } from './services/models/despacho.types';

export type Tono = 'success' | 'warning' | 'urgent' | 'critical' | 'info';

export const ESTADO_DESPACHO_TONO: Record<EstadoDespacho, Tono> = {
  Pendiente: 'warning',
  Confirmado: 'success',
  Rechazado: 'critical',
  Timeout: 'critical',
  Abortado: 'critical',
  En_sitio: 'success',
  Retirado: 'info',
};

export const ESTADO_NOTIFICACION_TONO: Record<EstadoNotificacion, Tono> = {
  Pendiente: 'warning',
  Notificada: 'info',
  Confirmada: 'success',
  Rechazada: 'critical',
  No_entregada: 'critical',
};

export function estadoDespachoTono(estado: EstadoDespacho): Tono {
  return ESTADO_DESPACHO_TONO[estado] ?? 'info';
}

export function estadoNotificacionTono(estado: EstadoNotificacion): Tono {
  return ESTADO_NOTIFICACION_TONO[estado] ?? 'info';
}
