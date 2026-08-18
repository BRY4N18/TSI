import { DefinicionPantalla } from '../models/informes-compuestos.types';

/** Los 13 slugs que el backend publica. El alcance geográfico no existe. */
export const PUBLICADOS_UI: readonly string[] = [
  'metricas-consumo',
  'reporte-mensual-consumo',
  'consumo-por-endpoint',
  'latencia-p95',
  'taxonomia-errores',
  'comparativa',
  'participacion-ingresos-api',
  'motivo-credencial-inactiva',
  'tiempo-incorporacion',
  'adopcion-versiones',
  'tasa-rechazo-produccion',
  'clientes-integracion-activa',
  'volumen-expedientes',
];

export const SLOTS_CONSUMO = [
  'latencia-p95',
  'taxonomia-errores',
  'comparativa',
  'metricas-consumo',
  'reporte-mensual-consumo',
  'consumo-por-endpoint',
  'participacion-ingresos-api',
] as const;

export const SLOTS_INCORPORACION = [
  'adopcion-versiones',
  'motivo-credencial-inactiva',
  'tiempo-incorporacion',
  'tasa-rechazo-produccion',
] as const;

export const SLOTS_ENTREGA = [
  'clientes-integracion-activa',
  'volumen-expedientes',
] as const;

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  consumo: {
    id: 'consumo',
    titulo: 'Consumo de la API',
    pregunta: '¿Cuánto se usa y cómo de lenta y errática es?',
    heroe: { informes: ['latencia-p95'], titulo: 'Latencia p95, media y muestras' },
    visual: { informes: ['taxonomia-errores'], titulo: 'Errores por clase' },
    lectura: { informes: ['comparativa'], titulo: 'Comparativa entre partners' },
    apoyo: {
      informes: [
        'metricas-consumo',
        'reporte-mensual-consumo',
        'consumo-por-endpoint',
        'participacion-ingresos-api',
      ],
      titulo: 'Detalle',
    },
    apoyoPlegado: true,
  },
  incorporacion: {
    id: 'incorporacion',
    titulo: 'Incorporación',
    pregunta: '¿Por qué no llega a producción y qué contrato usa?',
    heroe: { informes: ['adopcion-versiones'], titulo: 'Adopción de versiones' },
    visual: { informes: ['motivo-credencial-inactiva'], titulo: 'Motivo de credencial inactiva' },
    lectura: { informes: ['tiempo-incorporacion'], titulo: 'Tiempo de incorporación' },
    apoyo: { informes: ['tasa-rechazo-produccion'], titulo: 'Detalle' },
    apoyoPlegado: true,
  },
  entrega: {
    id: 'entrega',
    titulo: 'Entrega contratada',
    pregunta: '¿Cuántos clientes ya integran y por qué canal?',
    heroe: {
      informes: ['clientes-integracion-activa'],
      titulo: 'Clientes con integración activa',
    },
    visual: { informes: ['volumen-expedientes'], titulo: 'Expedientes por canal' },
    lectura: {
      informes: ['clientes-integracion-activa'],
      titulo: 'Qué implicaría un 100 %',
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
