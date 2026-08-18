import { DefinicionPantalla } from '../models/informes-compuestos.types';

/**
 * Los 13 slugs que el backend publica. Cada uno entra en exactamente una zona.
 */
export const PUBLICADOS_UI: readonly string[] = [
  'embudo-conversion',
  'permanencia-por-etapa',
  'carga-por-ejecutivo',
  'pipeline-ponderado',
  'motivos-perdida',
  'captacion-por-canal',
  'conversion-por-canal',
  'convertidos-por-canal',
  'intensidad-demo',
  'secciones-visitadas',
  'efectividad-nutricion',
  'latencia-reaccion',
  'reglas-disparo',
];

export const SLOTS_EMBUDO = [
  'embudo-conversion',
  'permanencia-por-etapa',
  'motivos-perdida',
  'carga-por-ejecutivo',
  'pipeline-ponderado',
] as const;

export const SLOTS_CAPTACION = [
  'captacion-por-canal',
  'conversion-por-canal',
  'convertidos-por-canal',
] as const;

export const SLOTS_NUTRICION = [
  'efectividad-nutricion',
  'intensidad-demo',
  'secciones-visitadas',
  'latencia-reaccion',
  'reglas-disparo',
] as const;

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  embudo: {
    id: 'embudo',
    titulo: 'Embudo comercial',
    pregunta: '¿Dónde se atasca y se pierde el pipeline?',
    heroe: {
      informes: ['embudo-conversion'],
      titulo: 'Paso entre etapas',
    },
    visual: {
      informes: ['permanencia-por-etapa'],
      titulo: 'Permanencia por etapa',
    },
    lectura: {
      informes: ['motivos-perdida'],
      titulo: 'Motivos de pérdida',
    },
    apoyo: {
      informes: ['carga-por-ejecutivo', 'pipeline-ponderado'],
      titulo: 'Detalle',
    },
    apoyoPlegado: true,
  },
  captacion: {
    id: 'captacion',
    titulo: 'Captación por canal',
    pregunta: '¿Por dónde entran y cuáles convierten?',
    heroe: {
      informes: ['captacion-por-canal'],
      titulo: 'Volumen por canal',
    },
    visual: {
      informes: ['conversion-por-canal'],
      titulo: 'Tasa de conversión por canal',
    },
    lectura: {
      informes: ['convertidos-por-canal'],
      titulo: 'Clientes convertidos por canal',
    },
  },
  nutricion: {
    id: 'nutricion',
    titulo: 'Nutrición del prospecto',
    pregunta: '¿La demo y el aviso mueven el embudo?',
    heroe: {
      informes: ['efectividad-nutricion'],
      titulo: 'Efectividad con demo y sin demo',
    },
    visual: {
      informes: ['intensidad-demo', 'secciones-visitadas'],
      titulo: 'Uso de la demo',
    },
    lectura: {
      informes: ['latencia-reaccion'],
      titulo: 'Latencia de reacción',
    },
    apoyo: {
      informes: ['reglas-disparo'],
      titulo: 'Detalle',
    },
    apoyoPlegado: true,
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
