import { DefinicionPantalla } from '../models/informes-oe5.types';

export const PUBLICADOS_UI: readonly string[] = [
  'cumplimiento-sla',
  'evolucion-incumplimiento',
  'sla-por-plan',
  'retencion-neta-ingresos',
  'movimientos-de-plan',
  'rendimiento-por-agente',
  'reincidencia-soporte',
  'cuentas-en-riesgo',
  'antiguedad-de-cuenta',
];

export const BLOQUEADOS_UI: readonly string[] = [
  'nps-satisfaccion',
  'reportes-sin-correccion',
  'tasa-renovacion',
  'churn-por-cohorte',
  'tiempo-onboarding',
  'abandono-onboarding',
];

export const SLOTS_SERVICIO = [
  'cumplimiento-sla',
  'evolucion-incumplimiento',
  'rendimiento-por-agente',
  'reincidencia-soporte',
] as const;

export const SLOTS_INGRESOS = ['retencion-neta-ingresos'] as const;

export const SLOTS_PLANES = [
  'sla-por-plan',
  'movimientos-de-plan',
  'antiguedad-de-cuenta',
] as const;

export const SLOTS_RIESGO = ['cuentas-en-riesgo'] as const;

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  servicio: {
    id: 'servicio',
    titulo: 'Compromiso de servicio',
    pregunta: '¿Se cumple el compromiso de tiempo?',
    heroe: { informes: ['cumplimiento-sla'], titulo: 'SLA con recuento' },
    visual: { informes: ['evolucion-incumplimiento'], titulo: 'Evolución del incumplimiento' },
    lectura: { informes: ['cumplimiento-sla'], titulo: 'Sin compromiso, aparte' },
    apoyo: {
      informes: ['rendimiento-por-agente', 'reincidencia-soporte'],
      titulo: 'Carga y reincidencia',
    },
    apoyoPlegado: true,
  },
  ingresos: {
    id: 'ingresos',
    titulo: 'Ingresos retenidos',
    pregunta: '¿La cartera crece o se erosiona?',
    heroe: { informes: ['retencion-neta-ingresos'], titulo: 'NRR neto' },
    visual: { informes: ['retencion-neta-ingresos'], titulo: 'Expansión, contracción y churn' },
    lectura: { informes: ['retencion-neta-ingresos'], titulo: 'Precio congelado, no catálogo' },
  },
  planes: {
    id: 'planes',
    titulo: 'Planes y antigüedad',
    pregunta: '¿El plan pagado recibe lo pagado, y cuánto duran las cuentas?',
    heroe: { informes: ['sla-por-plan'], titulo: 'SLA por plan' },
    visual: { informes: ['movimientos-de-plan'], titulo: 'Movimientos aprobados' },
    lectura: { informes: ['antiguedad-de-cuenta'], titulo: 'Antigüedad de activas' },
  },
  riesgo: {
    id: 'riesgo',
    titulo: 'Cuentas en riesgo',
    pregunta: '¿Qué cuenta se está yendo de verdad?',
    heroe: { informes: ['cuentas-en-riesgo'], titulo: 'Cuentas con ≥2 señales' },
    visual: { informes: ['cuentas-en-riesgo'], titulo: 'Señales presentes' },
    lectura: { informes: ['cuentas-en-riesgo'], titulo: 'Fuentes faltantes; una señal no basta' },
  },
};

export function definicionDe(id: string | null | undefined): DefinicionPantalla | null {
  if (!id) {
    return null;
  }
  return PANTALLAS[id] ?? null;
}

export function informesDe(def: DefinicionPantalla): string[] {
  const slugs = [
    ...def.heroe.informes,
    ...def.visual.informes,
    ...def.lectura.informes,
    ...(def.apoyo?.informes ?? []),
  ];
  return [...new Set(slugs)];
}
