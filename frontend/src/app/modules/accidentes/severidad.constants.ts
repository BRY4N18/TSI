import { TablerIconName } from '../../shared/ui/icon/tabler-icon.component';

export interface SeveridadInfo {
  value: number;
  label: string;
  icon: TablerIconName;
  tone: 'success' | 'warning' | 'urgent' | 'critical';
}

export const SEVERIDADES: SeveridadInfo[] = [
  { value: 1, label: 'Leve', icon: 'circle-check', tone: 'success' },
  { value: 2, label: 'Moderado', icon: 'alert-circle', tone: 'warning' },
  { value: 3, label: 'Grave', icon: 'alert-triangle', tone: 'urgent' },
  { value: 4, label: 'Fatal', icon: 'alert-octagon', tone: 'critical' },
];

export const SEVERIDAD_INFO: Record<number, SeveridadInfo> = Object.fromEntries(
  SEVERIDADES.map((s) => [s.value, s]),
);
