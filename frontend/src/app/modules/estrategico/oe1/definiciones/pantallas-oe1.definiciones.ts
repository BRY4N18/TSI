import { DefinicionPantalla } from '../models/informes-oe1.types';

export const PUBLICADOS_UI: readonly string[] = [
  'mrr-mensual',
  'arr-proyeccion',
  'tasa-renovacion',
  'cartera-por-plan',
  'mrr-por-segmento',
  'embudo-conversion',
  'velocidad-ciclo-venta',
  'churn-por-cohorte',
  'abandono-onboarding',
  'tiempo-onboarding',
];

export const BLOQUEADOS_UI: readonly string[] = [
  'cac-por-canal',
  'mercados-activos',
  'cartera-mrr-por-mercado',
];

export const SLOTS_INGRESO = [
  'mrr-mensual',
  'arr-proyeccion',
  'tasa-renovacion',
] as const;

export const SLOTS_CARTERA = ['cartera-por-plan', 'mrr-por-segmento'] as const;

export const SLOTS_CAPTACION = ['embudo-conversion', 'velocidad-ciclo-venta'] as const;

export const SLOTS_CICLO = [
  'churn-por-cohorte',
  'abandono-onboarding',
  'tiempo-onboarding',
] as const;

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  ingreso: {
    id: 'ingreso',
    titulo: 'Ingreso recurrente',
    pregunta: '¿Cuánto ingreso recurrente hay y se renueva?',
    heroe: { informes: ['mrr-mensual'], titulo: 'MRR con recuento' },
    visual: { informes: ['mrr-mensual'], titulo: 'Variación frente al período comparado' },
    lectura: { informes: ['arr-proyeccion'], titulo: 'ARR: extrapolación, no compromiso' },
    apoyo: { informes: ['tasa-renovacion'], titulo: 'Renovación sobre vencidas' },
    apoyoPlegado: true,
  },
  cartera: {
    id: 'cartera',
    titulo: 'Cartera',
    pregunta: '¿De qué tipo y de qué plan sale el ingreso?',
    heroe: { informes: ['cartera-por-plan'], titulo: 'Mezcla por plan' },
    visual: { informes: ['cartera-por-plan'], titulo: 'Evolución de la mezcla' },
    lectura: { informes: ['mrr-por-segmento'], titulo: 'Segmento = tipo, no país' },
  },
  captacion: {
    id: 'captacion',
    titulo: 'Captación',
    pregunta: '¿Cómo llega el cliente y cuánto tarda?',
    heroe: { informes: ['embudo-conversion'], titulo: 'Volumen del embudo' },
    visual: { informes: ['embudo-conversion'], titulo: 'Etapas, ceros visibles' },
    lectura: { informes: ['embudo-conversion'], titulo: 'Cruce Ventas–Cuentas' },
    apoyo: { informes: ['velocidad-ciclo-venta'], titulo: 'Velocidad por etapa y ejecutivo' },
    apoyoPlegado: true,
  },
  ciclo: {
    id: 'ciclo',
    titulo: 'Ciclo de vida',
    pregunta: '¿Dónde se pierde al cliente?',
    heroe: { informes: ['churn-por-cohorte'], titulo: 'Churn por cohorte' },
    visual: { informes: ['abandono-onboarding'], titulo: 'Abandono contra el catálogo' },
    lectura: { informes: ['tiempo-onboarding'], titulo: 'Tiempo: en proceso aparte' },
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
