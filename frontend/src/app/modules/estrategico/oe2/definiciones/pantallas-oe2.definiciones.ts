import { DefinicionPantalla } from '../models/informes-oe2.types';

export const PUBLICADOS_UI: readonly string[] = [
  'integraciones-activas',
  'consumo-por-partner',
  'latencia-por-endpoint',
  'taxonomia-errores',
  'excedente-facturable',
  'participacion-ingresos-api',
  'mrr-por-linea',
  'adopcion-versiones',
  'comparativa-partners',
  'crecimiento-ecosistema',
];

export const SLOTS_USO = [
  'integraciones-activas',
  'taxonomia-errores',
  'consumo-por-partner',
  'latencia-por-endpoint',
] as const;

export const SLOTS_DINERO = [
  'excedente-facturable',
  'participacion-ingresos-api',
  'mrr-por-linea',
] as const;

export const SLOTS_ECOSISTEMA = [
  'crecimiento-ecosistema',
  'adopcion-versiones',
  'comparativa-partners',
] as const;

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  uso: {
    id: 'uso',
    titulo: 'Uso de la API',
    pregunta: '¿Se usa y cómo responde?',
    heroe: { informes: ['integraciones-activas'], titulo: 'Adopción con acceso concedido' },
    visual: { informes: ['taxonomia-errores'], titulo: '4xx y 5xx por separado' },
    lectura: { informes: ['consumo-por-partner'], titulo: 'Consumo frente al cupo' },
    apoyo: { informes: ['latencia-por-endpoint'], titulo: 'Latencia p95, media y muestras' },
    apoyoPlegado: true,
  },
  dinero: {
    id: 'dinero',
    titulo: 'Dinero de la API',
    pregunta: '¿Cuánto se puede facturar y qué peso tiene?',
    heroe: { informes: ['excedente-facturable'], titulo: 'Excedente facturable' },
    visual: { informes: ['excedente-facturable'], titulo: 'Partners no tarificables' },
    lectura: { informes: ['excedente-facturable'], titulo: 'Alcance: no afirma cobro' },
    apoyo: {
      informes: ['participacion-ingresos-api', 'mrr-por-linea'],
      titulo: 'Participación y MRR (parcial)',
    },
    apoyoPlegado: true,
  },
  ecosistema: {
    id: 'ecosistema',
    titulo: 'Ecosistema',
    pregunta: '¿Quién usa qué contrato y si crece?',
    heroe: { informes: ['crecimiento-ecosistema'], titulo: 'Primera llamada exitosa' },
    visual: { informes: ['adopcion-versiones'], titulo: 'Adopción por servicio y versión' },
    lectura: { informes: ['comparativa-partners'], titulo: 'Comparativa' },
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
