import { EstadoAccidente } from './services/models/accidente.types';

export interface EstadoInfo {
  label: string;
  tone: 'success' | 'warning' | 'urgent' | 'info';
}

export const ESTADO_INFO: Record<EstadoAccidente, EstadoInfo> = {
  BORRADOR: { label: 'BORRADOR', tone: 'info' },
  REPORTADO: { label: 'REPORTADO', tone: 'info' },
  BUSCANDO_UNIDAD: { label: 'BUSCANDO_UNIDAD', tone: 'warning' },
  ASIGNADO: { label: 'ASIGNADO', tone: 'warning' },
  EN_ATENCIÓN: { label: 'EN_ATENCIÓN', tone: 'urgent' },
  CERRADO: { label: 'CERRADO', tone: 'success' },
  DESCARTADO: { label: 'DESCARTADO', tone: 'info' },
  FUSIONADO: { label: 'FUSIONADO', tone: 'info' },
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
