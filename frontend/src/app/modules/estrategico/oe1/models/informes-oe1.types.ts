/** Tipos de pantalla OE1. Las cifras viven en el backend. */

export type IdPantalla = 'ingreso' | 'cartera' | 'captacion' | 'ciclo';

export type EstadoZona = 'carga' | 'dato' | 'vacio' | 'error' | 'sin_dato';

export type Granularidad = 'mes' | 'trimestre' | 'anio';

export type Comparacion = 'ninguna' | 'mom' | 'yoy';

export interface PeriodoVista {
  desde: string;
  hasta: string;
  granularidad: Granularidad;
  comparacion: Comparacion;
}

export interface MetaInforme {
  periodo?: { desde?: string; hasta?: string; granularidad?: string };
  comparacion?: Record<string, unknown> | null;
  objetivo?: Record<string, unknown> | null;
  cobertura?: 'completa' | 'parcial';
  falta?: string[];
  alcance?: string | null;
  motivo_ausencia?: string;
}

export interface EnvelopeInforme {
  data: Record<string, unknown>[] | { resultados?: Record<string, unknown>[] } | null;
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

export function extraerFilas(data: EnvelopeInforme['data']): Record<string, unknown>[] {
  if (Array.isArray(data)) {
    return data;
  }
  if (data && Array.isArray(data.resultados)) {
    return data.resultados;
  }
  return [];
}
