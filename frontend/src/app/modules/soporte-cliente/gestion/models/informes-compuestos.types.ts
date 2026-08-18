/** Tipos de pantalla. El almacén y las cifras viven en el backend. */

export type IdPantalla = 'cumplimiento' | 'cola' | 'tendencias';

export type EstadoZona = 'carga' | 'dato' | 'vacio' | 'error' | 'sin_dato';

export type AlcanceVista = 'todos' | 'propios';

export type AgruparCola = 'estado' | 'prioridad' | 'tipo' | 'agente';

export interface PeriodoVista {
  desde: string;
  hasta: string;
}

export interface DeclaracionInforme {
  codigo?: string;
  mensaje?: string;
}

export interface CuerpoInforme {
  resultados?: Record<string, unknown>[];
  declaraciones?: DeclaracionInforme[];
  periodo?: { desde?: string | null; hasta?: string | null; acotado?: boolean };
}

export interface MetaInforme {
  periodo?: { desde?: string; hasta?: string; granularidad?: string };
  filtros?: Record<string, unknown>;
  acotado_a?: AlcanceVista | string;
}

/**
 * ⚠️ El envelope de Soporte no es el de Ventas: `data` es un objeto con
 * `resultados` y `declaraciones`, no un array.
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
  declaraciones: DeclaracionInforme[];
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

export function extraerDeclaraciones(data: EnvelopeInforme['data']): DeclaracionInforme[] {
  if (!data || Array.isArray(data) || !Array.isArray(data.declaraciones)) {
    return [];
  }
  return data.declaraciones;
}
