/** Tipos de pantalla. El almacén y las cifras viven en el backend. */

export type IdPantalla = 'calidad' | 'despacho' | 'cierre';

export type EstadoZona = 'carga' | 'dato' | 'vacio' | 'error' | 'sin_dato';

export interface PeriodoVista {
  desde: string;
  hasta: string;
}

export interface MetaInforme {
  periodo?: { desde: string; hasta: string };
  filtros?: Record<string, unknown>;
  nota_referencia?: string;
  nota?: string;
  alcance?: string;
  cobertura?: string;
}

export interface EnvelopeInforme {
  data: Record<string, unknown>[];
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
  camposComprobados?: readonly string[];
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
