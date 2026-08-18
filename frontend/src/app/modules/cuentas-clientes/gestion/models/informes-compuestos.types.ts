/** Tipos de pantalla. El almacén y las cifras viven en el backend. */

export type IdPantalla = 'ciclo' | 'incorporacion' | 'acceso';

export type Materia = 'ciclo' | 'incorporacion' | 'acceso';

export type EstadoZona = 'carga' | 'dato' | 'vacio' | 'error' | 'sin_dato';

export interface PeriodoVista {
  desde: string;
  hasta: string;
}

export interface CuerpoInforme {
  resultados?: Record<string, unknown>[];
  periodo?: { desde?: string; hasta?: string };
}

export interface MetaInforme {
  periodo?: { desde: string; hasta: string };
  filtros?: Record<string, unknown>;
  nota_cobertura?: string;
  nota_catalogo?: string;
  nota_solape?: string;
}

/**
 * ⚠️ El envelope de Cuentas no es un array: `data` trae `resultados`.
 * Cobertura, catálogo y solape viajan en `meta`.
 */
export interface EnvelopeInforme {
  data: CuerpoInforme | Record<string, unknown>[] | null;
  meta: MetaInforme;
}

export interface ZonaDefinicion {
  informes: string[];
  titulo: string;
}

export interface DefinicionPantalla {
  id: IdPantalla;
  titulo: string;
  pregunta: string;
  materia: Materia;
  heroe: ZonaDefinicion;
  visual: ZonaDefinicion;
  lectura: ZonaDefinicion;
  apoyo?: ZonaDefinicion;
  apoyoPlegado?: boolean;
}

export interface CargaInforme {
  estado: EstadoZona;
  error: string | null;
  data: Record<string, unknown>[];
  meta: MetaInforme;
}

export function num(valor: unknown): number | null {
  if (valor === null || valor === undefined || valor === '') {
    return null;
  }
  const n = Number(valor);
  return Number.isFinite(n) ? n : null;
}

export function texto(valor: unknown): string {
  if (valor === null || valor === undefined) {
    return '';
  }
  return String(valor);
}

export function extraerResultados(
  data: EnvelopeInforme['data'],
): Record<string, unknown>[] {
  if (Array.isArray(data)) {
    return data as Record<string, unknown>[];
  }
  if (data && Array.isArray(data.resultados)) {
    return data.resultados;
  }
  return [];
}
