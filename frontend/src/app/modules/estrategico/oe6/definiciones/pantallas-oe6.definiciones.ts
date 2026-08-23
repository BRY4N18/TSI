import { DefinicionPantalla } from '../models/informes-oe6.types';

export const PUBLICADOS_UI: readonly string[] = [
  'tiempo-respuesta-global',
  'tiempo-respuesta-por-severidad',
  'tramos-del-ciclo',
  'origen-de-asignacion',
  'rechazo-y-timeout-por-unidad',
  'abortos-y-misiones-fallidas',
  'desviacion-de-llegada',
  'impacto-humano',
  'cierres-forzados',
  'envejecimiento-de-casos-abiertos',
  'escaladas-de-severidad',
  'cobertura-de-evidencia',
];

export const BLOQUEADOS_UI: readonly string[] = ['eta', 'mapa', 'latencia-asignacion'];

export const SLOTS_LLEGADA = [
  'tiempo-respuesta-global',
  'tiempo-respuesta-por-severidad',
] as const;

export const SLOTS_DIAGNOSTICO = [
  'tramos-del-ciclo',
  'origen-de-asignacion',
  'desviacion-de-llegada',
] as const;

export const SLOTS_EJECUCION = [
  'envejecimiento-de-casos-abiertos',
  'rechazo-y-timeout-por-unidad',
  'abortos-y-misiones-fallidas',
  'cierres-forzados',
] as const;

export const SLOTS_PERSONAS = [
  'impacto-humano',
  'escaladas-de-severidad',
  'cobertura-de-evidencia',
] as const;

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  llegada: {
    id: 'llegada',
    titulo: 'Tiempo de llegada',
    pregunta: '¿Cuánto tarda en llegar la ayuda?',
    heroe: { informes: ['tiempo-respuesta-global'], titulo: 'Mediana y p95' },
    visual: { informes: ['tiempo-respuesta-por-severidad'], titulo: 'Por severidad' },
    lectura: { informes: ['tiempo-respuesta-global'], titulo: 'Sin llegada, aparte' },
  },
  diagnostico: {
    id: 'diagnostico',
    titulo: 'Dónde se va el tiempo',
    pregunta: '¿En qué tramo se pierde la respuesta?',
    heroe: { informes: ['tramos-del-ciclo'], titulo: 'Tramos del ciclo' },
    visual: { informes: ['origen-de-asignacion'], titulo: 'Automático vs manual' },
    lectura: { informes: ['desviacion-de-llegada'], titulo: 'Vs histórico, no ETA' },
  },
  ejecucion: {
    id: 'ejecucion',
    titulo: 'Ejecución del despacho',
    pregunta: '¿Qué falla al despachar?',
    heroe: { informes: ['envejecimiento-de-casos-abiertos'], titulo: 'Abiertos que envejecen' },
    visual: {
      informes: ['rechazo-y-timeout-por-unidad', 'abortos-y-misiones-fallidas'],
      titulo: 'Rechazo y abortos',
    },
    lectura: { informes: ['cierres-forzados'], titulo: 'Cierres forzados (definición)' },
    apoyo: {
      informes: ['rechazo-y-timeout-por-unidad'],
      titulo: 'Tasas con denominador',
    },
    apoyoPlegado: true,
  },
  personas: {
    id: 'personas',
    titulo: 'Personas atendidas',
    pregunta: '¿Qué pasó con quien esperaba?',
    heroe: { informes: ['impacto-humano'], titulo: 'Impacto humano' },
    visual: { informes: ['escaladas-de-severidad'], titulo: 'Escaladas en sitio' },
    lectura: { informes: ['cobertura-de-evidencia'], titulo: 'Evidencia en cerrados' },
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
