import { DefinicionPantalla } from '../models/informes-oe4.types';

export const PUBLICADOS_UI: readonly string[] = [
  'indice-calidad-historico',
  'completitud-campos-criticos',
  'campos-mas-ausentes',
  'calidad-por-origen',
  'concentracion-siniestralidad',
  'patron-horario-climatico',
  'impacto-humano-por-zona',
  'impacto-vial-por-zona',
  'cobertura-del-historico',
];

export const BLOQUEADOS_UI: readonly string[] = [
  'precision-del-modelo',
  'contraste-prediccion-ocurrencia',
  'unidades-preposicionadas',
  'versiones-del-modelo',
  'productos-de-inteligencia',
  'latencia-de-ingesta',
];

export const SLOTS_CALIDAD = [
  'indice-calidad-historico',
  'completitud-campos-criticos',
  'campos-mas-ausentes',
  'calidad-por-origen',
] as const;

export const SLOTS_CONCENTRACION = [
  'concentracion-siniestralidad',
  'patron-horario-climatico',
] as const;

export const SLOTS_IMPACTO = ['impacto-humano-por-zona', 'impacto-vial-por-zona'] as const;

export const SLOTS_COBERTURA = ['cobertura-del-historico'] as const;

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  calidad: {
    id: 'calidad',
    titulo: 'Calidad del histórico',
    pregunta: '¿El registro es fiable para vender inteligencia?',
    heroe: { informes: ['indice-calidad-historico'], titulo: 'Índice y sus cuatro piezas' },
    visual: { informes: ['completitud-campos-criticos'], titulo: 'Completitud de campos críticos' },
    lectura: { informes: ['campos-mas-ausentes'], titulo: 'Ausencias (también las que valen 0)' },
    apoyo: { informes: ['calidad-por-origen'], titulo: 'Central vs campo' },
    apoyoPlegado: true,
  },
  concentracion: {
    id: 'concentracion',
    titulo: 'Concentración de siniestralidad',
    pregunta: '¿Dónde y cuándo se acumulan los casos?',
    heroe: { informes: ['concentracion-siniestralidad'], titulo: 'Ranking por zona (nombre)' },
    visual: { informes: ['patron-horario-climatico'], titulo: 'Horario y clima (parcial)' },
    lectura: { informes: ['concentracion-siniestralidad'], titulo: 'No es un mapa' },
  },
  impacto: {
    id: 'impacto',
    titulo: 'Impacto humano y vial',
    pregunta: '¿A quién y a qué vía afecta?',
    heroe: { informes: ['impacto-humano-por-zona'], titulo: 'Víctimas con dato' },
    visual: { informes: ['impacto-vial-por-zona'], titulo: 'Duración y distancia' },
    lectura: { informes: ['impacto-humano-por-zona'], titulo: 'No-dato no es cero' },
  },
  cobertura: {
    id: 'cobertura',
    titulo: 'Cobertura del histórico',
    pregunta: '¿Hay masa crítica por condado para entrenar?',
    heroe: { informes: ['cobertura-del-historico'], titulo: 'Casos vs umbral' },
    visual: { informes: ['cobertura-del-historico'], titulo: 'Condados sin masa crítica' },
    lectura: { informes: ['cobertura-del-historico'], titulo: 'Umbral publicado · grano condado' },
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
