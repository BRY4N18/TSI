import { DefinicionPantalla } from '../models/informes-oe3.types';

export const PUBLICADOS_UI: readonly string[] = [
  'latencia-asignacion',
  'evolucion-latencia',
  'tasa-error-registro',
  'primer-intento',
  'ratio-demanda-capacidad',
  'cobertura-de-respaldo',
  'perdida-de-senal',
];

export const BLOQUEADOS_UI: readonly string[] = [
  'uptime-por-region',
  'tiempo-puesta-operacion',
  'curva-maduracion',
  'cohorte-region',
  'margen-operativo',
  'reasignacion-manual',
  'cobertura-pruebas',
];

export const SLOTS_LATENCIA = ['latencia-asignacion', 'evolucion-latencia'] as const;

export const SLOTS_CALIDAD = ['tasa-error-registro', 'primer-intento'] as const;

export const SLOTS_CAPACIDAD = ['ratio-demanda-capacidad', 'perdida-de-senal'] as const;

export const SLOTS_RESPALDO = ['cobertura-de-respaldo'] as const;

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  latencia: {
    id: 'latencia',
    titulo: 'Latencia de despacho',
    pregunta: '¿El despacho se está volviendo más lento?',
    heroe: { informes: ['latencia-asignacion'], titulo: 'p95 registro → asignación' },
    visual: { informes: ['evolucion-latencia'], titulo: 'Evolución del p95' },
    lectura: { informes: ['latencia-asignacion'], titulo: 'Proceso operativo, no algoritmo' },
  },
  calidad: {
    id: 'calidad',
    titulo: 'Calidad del despacho',
    pregunta: '¿El registro y el primer intento aguantan?',
    heroe: { informes: ['tasa-error-registro'], titulo: 'Error de registro' },
    visual: { informes: ['primer-intento'], titulo: 'Primer intento (grano de intento)' },
    lectura: { informes: ['tasa-error-registro'], titulo: 'Campos comprobados' },
  },
  capacidad: {
    id: 'capacidad',
    titulo: 'Capacidad por condado',
    pregunta: '¿Dónde la demanda aprieta a la flota?',
    heroe: { informes: ['ratio-demanda-capacidad'], titulo: 'Demanda / capacidad' },
    visual: { informes: ['ratio-demanda-capacidad'], titulo: 'Tensos y sin capacidad' },
    lectura: { informes: ['ratio-demanda-capacidad'], titulo: 'Flota del período' },
    apoyo: { informes: ['perdida-de-senal'], titulo: 'Pérdida de señal GPS' },
    apoyoPlegado: true,
  },
  respaldo: {
    id: 'respaldo',
    titulo: 'Respaldo vecinal',
    pregunta: '¿El condado vecino puede cubrir?',
    heroe: { informes: ['cobertura-de-respaldo'], titulo: 'Cobertura de respaldo' },
    visual: { informes: ['cobertura-de-respaldo'], titulo: 'Disponible vs solo alta' },
    lectura: { informes: ['cobertura-de-respaldo'], titulo: 'Denominador a la vista' },
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
