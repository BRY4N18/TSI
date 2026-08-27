import { EstadoAccidente } from './services/models/accidente.types';

export interface EstadoInfo {
  label: string;
  tone: 'success' | 'warning' | 'urgent' | 'info';
}

export const ESTADO_INFO: Record<EstadoAccidente, EstadoInfo> = {
  BORRADOR: { label: 'Borrador', tone: 'info' },
  REPORTADO: { label: 'Reportado', tone: 'info' },
  BUSCANDO_UNIDAD: { label: 'Buscando unidad', tone: 'warning' },
  ASIGNADO: { label: 'Asignado', tone: 'warning' },
  EN_ATENCIÓN: { label: 'En atención', tone: 'urgent' },
  CERRADO: { label: 'Cerrado', tone: 'success' },
  DESCARTADO: { label: 'Descartado', tone: 'info' },
  FUSIONADO: { label: 'Fusionado', tone: 'info' },
};

export const ESTADOS: EstadoAccidente[] = [
  'BORRADOR',
  'REPORTADO',
  'BUSCANDO_UNIDAD',
  'ASIGNADO',
  'EN_ATENCIÓN',
  'CERRADO',
  'DESCARTADO',
  'FUSIONADO',
];

export function estadoInfo(estado: EstadoAccidente | null | undefined): EstadoInfo {
  return estado && ESTADO_INFO[estado] ? ESTADO_INFO[estado] : { label: 'Desconocido', tone: 'info' };
}
