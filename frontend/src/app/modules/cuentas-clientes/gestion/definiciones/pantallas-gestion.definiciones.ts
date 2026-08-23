import { DefinicionPantalla } from '../models/informes-compuestos.types';

/** Los 8 slugs que el backend publica.
 *
 * ⚠️ Eran 9. `roles-incompatibles` se retiró el 2026-08-23: recibía los pares de
 * roles incompatibles por parámetro y **ninguna pantalla los enviaba**, así que
 * su consulta devolvía cero filas por construcción, siempre.
 */
export const PUBLICADOS_UI: readonly string[] = [
  'churn-por-cohorte',
  'antiguedad-media',
  'usuarios-vs-tope',
  'cuentas-en-riesgo',
  'tiempo-onboarding',
  'embudo-abandono',
  'tasa-aprobacion',
  'concurrencia-sesiones',
];

export const SLOTS_CICLO = [
  'churn-por-cohorte',
  'usuarios-vs-tope',
  'cuentas-en-riesgo',
  'antiguedad-media',
] as const;

export const SLOTS_INCORPORACION = [
  'tiempo-onboarding',
  'embudo-abandono',
  'tasa-aprobacion',
] as const;

export const SLOTS_ACCESO = ['concurrencia-sesiones'] as const;

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  ciclo: {
    id: 'ciclo',
    titulo: 'Ciclo de vida',
    pregunta: '¿Quién se va y quién está al límite?',
    materia: 'ciclo',
    heroe: { informes: ['churn-por-cohorte'], titulo: 'Churn por cohorte de alta' },
    visual: {
      informes: ['usuarios-vs-tope'],
      titulo: 'Ocupación frente al tope, con cobertura',
    },
    lectura: { informes: ['cuentas-en-riesgo'], titulo: 'Cuentas en riesgo' },
    apoyo: { informes: ['antiguedad-media'], titulo: 'Detalle' },
    apoyoPlegado: true,
  },
  incorporacion: {
    id: 'incorporacion',
    titulo: 'Incorporación',
    pregunta: '¿Dónde se atasca el alta?',
    materia: 'incorporacion',
    heroe: { informes: ['tiempo-onboarding'], titulo: 'Tiempo de onboarding' },
    visual: { informes: ['embudo-abandono'], titulo: 'Embudo de abandono' },
    lectura: { informes: ['tasa-aprobacion'], titulo: 'Tasa de aprobación' },
  },
  acceso: {
    id: 'acceso',
    titulo: 'Acceso',
    pregunta: '¿Cuánta gente entra a la vez y quién acumula de más?',
    materia: 'acceso',
    heroe: {
      informes: ['concurrencia-sesiones'],
      titulo: 'Concurrencia máxima por solape',
    },
    visual: { informes: ['concurrencia-sesiones'], titulo: 'Franjas horarias' },
    apoyo: { informes: ['concurrencia-sesiones'], titulo: 'Duración y sesiones abiertas' },
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
    ...(def.lectura?.informes ?? []),
    ...(def.apoyo?.informes ?? []),
  ];
  return [...new Set(slugs)];
}
