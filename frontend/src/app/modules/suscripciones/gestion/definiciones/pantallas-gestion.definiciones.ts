import { DefinicionPantalla } from '../models/informes-compuestos.types';

/**
 * Los 13 slugs que el backend publica. Cada uno entra en exactamente una zona.
 */
export const PUBLICADOS_UI: readonly string[] = [
  'mrr',
  'ingresos',
  'tasa-renovacion',
  'cobro-primer-intento',
  'efectividad-dunning',
  'clientes-sin-metodo-pago',
  'movimientos-plan',
  'nrr',
  'suspension-reactivacion',
  'tiempo-resolucion-solicitudes',
  'distribucion-cartera',
  'utilizacion-limites',
  'severidades-habilitadas-vs-usadas',
];

export const SLOTS_COBRO = [
  'mrr',
  'ingresos',
  'tasa-renovacion',
  'cobro-primer-intento',
  'efectividad-dunning',
  'clientes-sin-metodo-pago',
] as const;

export const SLOTS_MOVIMIENTOS = [
  'nrr',
  'movimientos-plan',
  'tiempo-resolucion-solicitudes',
  'suspension-reactivacion',
] as const;

export const SLOTS_CATALOGO = [
  'distribucion-cartera',
  'utilizacion-limites',
  'severidades-habilitadas-vs-usadas',
] as const;

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  cobro: {
    id: 'cobro',
    titulo: 'Cobro e ingreso',
    pregunta: '¿Cuánto entra y se cobra?',
    materia: 'finanzas',
    heroe: { informes: ['mrr'], titulo: 'Ingreso recurrente mensual' },
    visual: { informes: ['ingresos'], titulo: 'Ingresos por plan' },
    lectura: { informes: ['tasa-renovacion'], titulo: 'Tasa de renovación' },
    apoyo: {
      informes: [
        'cobro-primer-intento',
        'efectividad-dunning',
        'clientes-sin-metodo-pago',
      ],
      titulo: 'Detalle',
    },
    apoyoPlegado: true,
  },
  movimientos: {
    id: 'movimientos',
    titulo: 'Movimientos de cartera',
    pregunta: '¿La cartera que ya está se sostiene?',
    materia: 'finanzas',
    heroe: { informes: ['nrr'], titulo: 'Retención neta de ingresos' },
    visual: { informes: ['movimientos-plan'], titulo: 'Upgrades y downgrades' },
    lectura: {
      informes: ['tiempo-resolucion-solicitudes'],
      titulo: 'Tiempo de resolución',
    },
    apoyo: {
      informes: ['suspension-reactivacion'],
      titulo: 'Detalle',
    },
    apoyoPlegado: true,
  },
  catalogo: {
    id: 'catalogo',
    titulo: 'Catálogo y uso',
    pregunta: '¿Pagan por lo que usan?',
    materia: 'catalogo',
    heroe: { informes: ['distribucion-cartera'], titulo: 'Distribución de cartera' },
    visual: { informes: ['utilizacion-limites'], titulo: 'Utilización de límites' },
    lectura: {
      informes: ['severidades-habilitadas-vs-usadas'],
      titulo: 'Severidades habilitadas y usadas',
    },
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
