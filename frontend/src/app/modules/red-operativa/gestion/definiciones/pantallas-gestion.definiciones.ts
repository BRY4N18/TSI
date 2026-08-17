import { DefinicionPantalla } from '../models/informes-compuestos.types';

/**
 * Los 15 slugs que el backend publica. Cada uno entra en exactamente una zona.
 */
export const PUBLICADOS_UI: readonly string[] = [
  'unidades-por-estado',
  'disponibilidad-declarada',
  'cobertura-flota-por-region',
  'condados-cobertura-critica',
  'rotacion-flota',
  'bajas-forzadas',
  'pendientes-primer-acceso',
  'rendimiento-proveedor',
  'tiempo-puesta-operacion',
  'mercados-activos',
  'tasa-aprobacion-primer-intento',
  'motivos-rechazo',
  'regiones-en-riesgo',
  'casos-activos-al-despublicar',
  'tiempo-perdida-a-despublicacion',
];

export const SLOTS_FLOTA = [
  'unidades-por-estado',
  'disponibilidad-declarada',
  'cobertura-flota-por-region',
  'condados-cobertura-critica',
  'rotacion-flota',
  'bajas-forzadas',
  'pendientes-primer-acceso',
  'rendimiento-proveedor',
] as const;

export const SLOTS_MERCADOS = [
  'tiempo-puesta-operacion',
  'mercados-activos',
  'regiones-en-riesgo',
  'casos-activos-al-despublicar',
  'tiempo-perdida-a-despublicacion',
] as const;

export const SLOTS_VALIDACION = [
  'tasa-aprobacion-primer-intento',
  'motivos-rechazo',
] as const;

/** D8: el grano no viene como columna; se declara aquí, igual que FR-017. */
export const TEXTO_GRANO =
  'Se cuentan intentos de validación, no regiones: una región aprobada al tercer intento no cuenta como aprobada al primero.';

export const TEXTO_CONVENCION_DIAS =
  'El objetivo en días es una convención de este informe: el sistema operativo no define ningún plazo de puesta en operación.';

export const TEXTO_CONVENCION_UMBRAL =
  'El umbral es una convención de este informe: el sistema operativo no define ninguna cobertura mínima.';

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  flota: {
    id: 'flota',
    titulo: 'Flota y cobertura',
    pregunta: '¿Hay quién atienda, y dónde falta?',
    materia: 'crecimiento',
    heroe: {
      informes: ['condados-cobertura-critica'],
      titulo: 'Condados en cobertura crítica',
    },
    visual: {
      informes: ['unidades-por-estado'],
      titulo: 'Unidades por estado',
    },
    lectura: {
      informes: ['disponibilidad-declarada'],
      titulo: 'Disponibilidad declarada',
    },
    apoyo: {
      informes: [
        'cobertura-flota-por-region',
        'pendientes-primer-acceso',
        'rendimiento-proveedor',
        'rotacion-flota',
        'bajas-forzadas',
      ],
      titulo: 'Detalle',
    },
    apoyoPlegado: true,
  },
  mercados: {
    id: 'mercados',
    titulo: 'Mercados y retirada',
    pregunta: '¿Dónde se abre y dónde se sostiene el mercado?',
    materia: 'crecimiento',
    heroe: {
      informes: ['mercados-activos'],
      titulo: 'Mercados activos',
    },
    visual: {
      informes: ['tiempo-puesta-operacion'],
      titulo: 'Tiempo de puesta en operación',
    },
    lectura: {
      informes: ['regiones-en-riesgo'],
      titulo: 'Regiones en riesgo',
    },
    apoyo: {
      informes: ['casos-activos-al-despublicar', 'tiempo-perdida-a-despublicacion'],
      titulo: 'Detalle',
    },
    apoyoPlegado: true,
  },
  validacion: {
    id: 'validacion',
    titulo: 'Criterios de validación',
    pregunta: '¿Se aprueba a la primera, y por qué se rechaza?',
    materia: 'validacion',
    lecturaTexto: TEXTO_GRANO,
    heroe: {
      informes: ['tasa-aprobacion-primer-intento'],
      titulo: 'Aprobación al primer intento',
    },
    visual: {
      informes: ['motivos-rechazo'],
      titulo: 'Motivos de rechazo',
    },
    lectura: {
      informes: [],
      titulo: 'Qué se está contando',
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
