import { DefinicionPantalla } from '../models/informes-compuestos.types';

/**
 * Los 9 slugs que el backend publica. Cada uno entra en exactamente una zona,
 * salvo `carga-entrante-resuelta` que alimenta héroe y visual (D10).
 */
export const PUBLICADOS_UI: readonly string[] = [
  'cumplimiento-sla',
  'cumplimiento-sla-por-plan',
  'rendimiento-agentes',
  'tickets-por-servicio',
  'tablero-cola',
  'evolucion-incumplimiento',
  'escalado-automatico',
  'carga-entrante-resuelta',
  'reincidencia-clientes',
];

/** D6: el id publicado no siempre coincide con el segmento HTTP. */
export const RUTA_HTTP: Record<string, string> = {
  'cumplimiento-sla': 'cumplimiento-sla',
  'cumplimiento-sla-por-plan': 'cumplimiento-sla/por-plan',
  'rendimiento-agentes': 'rendimiento-agentes',
  'tickets-por-servicio': 'tickets-por-servicio',
  'tablero-cola': 'tablero-cola',
  'evolucion-incumplimiento': 'evolucion-incumplimiento',
  'escalado-automatico': 'escalado-automatico',
  'carga-entrante-resuelta': 'carga-entrante-resuelta',
  'reincidencia-clientes': 'reincidencia-clientes',
};

export const SLOTS_CUMPLIMIENTO = [
  'cumplimiento-sla',
  'cumplimiento-sla-por-plan',
  'rendimiento-agentes',
  'tickets-por-servicio',
] as const;

export const SLOTS_COLA = [
  'tablero-cola',
  'evolucion-incumplimiento',
  'escalado-automatico',
] as const;

export const SLOTS_TENDENCIAS = [
  'carga-entrante-resuelta',
  'reincidencia-clientes',
] as const;

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  cumplimiento: {
    id: 'cumplimiento',
    titulo: 'Cumplimiento de SLA',
    pregunta: '¿Atendemos dentro de lo comprometido?',
    heroe: {
      informes: ['cumplimiento-sla'],
      titulo: 'Cumplimiento y cobertura',
    },
    visual: {
      informes: ['cumplimiento-sla-por-plan'],
      titulo: 'Cumplimiento por plan',
    },
    lectura: {
      informes: ['rendimiento-agentes'],
      titulo: 'Rendimiento por agente',
    },
    apoyo: {
      informes: ['tickets-por-servicio'],
      titulo: 'Tickets por servicio',
    },
    apoyoPlegado: true,
  },
  cola: {
    id: 'cola',
    titulo: 'Cola en curso',
    pregunta: '¿Qué pasa ahora y se está rompiendo el plazo?',
    heroe: {
      informes: ['tablero-cola'],
      titulo: 'Tablero de cola',
    },
    visual: {
      informes: ['evolucion-incumplimiento'],
      titulo: 'Evolución del incumplimiento',
    },
    lectura: {
      informes: ['escalado-automatico'],
      titulo: 'Escalado automático y humano',
    },
  },
  tendencias: {
    id: 'tendencias',
    titulo: 'Tendencias',
    pregunta: '¿La cola se acumula y quién repite?',
    heroe: {
      informes: ['carga-entrante-resuelta'],
      titulo: 'Saldo del día',
    },
    visual: {
      informes: ['carga-entrante-resuelta'],
      titulo: 'Carga entrante frente a resuelta',
    },
    lectura: {
      informes: ['reincidencia-clientes'],
      titulo: 'Reincidencia',
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

export function rutaHttpDe(informe: string): string {
  return RUTA_HTTP[informe] ?? informe;
}
