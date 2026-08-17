import { DefinicionPantalla } from '../models/informes-compuestos.types';

/**
 * Los 13 slugs que el backend publica. Pintar uno vigilado aquí duplicaría
 * una cifra que ya vive en el workpanel.
 */
export const PUBLICADOS_UI: readonly string[] = [
  'completitud-campos-criticos',
  'ratio-demanda-capacidad',
  'perdida-senal',
  'primer-intento',
  'desviacion-llegada',
  'cobertura-evidencia',
  'latencia-sincronizacion',
  'completitud-enriquecimiento',
  'volumen-evidencia-por-unidad',
  'escaladas-severidad',
  'distribucion-resultados',
  'envejecimiento-cartera',
  'retiros-forzados-por-proveedor',
];

export const VIGILADOS_UI: readonly string[] = [
  'tiempo-asignado-cierre',
  'cierres-forzados',
  'distribucion-severidad',
  'distribucion-zona',
  'descarte-fusion',
  'ranking-ubicaciones',
  'impacto-humano',
  'asignacion-automatica-vs-manual',
  'tiempo-reportado-confirmado',
  'tiempo-respuesta-por-severidad',
  'rechazo-timeout-por-unidad',
  'carga-por-unidad',
  'abortos-perdidas',
];

/** D6: el backend no emite la lista; se declara aquí, igual que FR-005. */
export const CAMPOS_COMPROBADOS_CALIDAD = ['severidad', 'condado'] as const;

export const TEXTO_NO_SLA =
  'Valor derivado del histórico; no es un objetivo ni un SLA.';

export const PANTALLAS: Record<string, DefinicionPantalla> = {
  calidad: {
    id: 'calidad',
    titulo: 'Calidad del registro',
    pregunta: '¿El expediente se está llenando de verdad?',
    camposComprobados: CAMPOS_COMPROBADOS_CALIDAD,
    heroe: {
      informes: ['completitud-campos-criticos'],
      titulo: 'Completitud de campos críticos',
    },
    visual: {
      informes: ['completitud-campos-criticos'],
      titulo: 'Completos e incompletos',
    },
    lectura: {
      informes: ['completitud-campos-criticos'],
      titulo: 'Qué se comprobó',
    },
  },
  despacho: {
    id: 'despacho',
    titulo: 'Despacho',
    pregunta: '¿El despacho se sostiene?',
    heroe: {
      informes: ['primer-intento'],
      titulo: 'Resolución al primer intento',
    },
    visual: {
      informes: ['desviacion-llegada'],
      titulo: 'Desviación de llegada',
    },
    lectura: {
      informes: ['perdida-senal'],
      titulo: 'Pérdida de señal',
    },
    apoyo: {
      informes: ['ratio-demanda-capacidad'],
      titulo: 'Demanda / capacidad',
    },
  },
  cierre: {
    id: 'cierre',
    titulo: 'Evidencia y cierre',
    pregunta: '¿Se cierra el ciclo con prueba y desenlace?',
    heroe: {
      informes: ['envejecimiento-cartera'],
      titulo: 'Cartera abierta',
    },
    visual: {
      informes: ['cobertura-evidencia'],
      titulo: 'Cobertura de evidencia',
    },
    lectura: {
      informes: ['distribucion-resultados', 'retiros-forzados-por-proveedor'],
      titulo: 'Resultados y retiros',
    },
    apoyo: {
      informes: [
        'latencia-sincronizacion',
        'completitud-enriquecimiento',
        'volumen-evidencia-por-unidad',
        'escaladas-severidad',
      ],
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
