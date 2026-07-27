export type TipoPropiedad = 'Propia' | 'Externa';

export type TipoUnidadEmergencia =
  | 'Ambulancia'
  | 'Grúa'
  | 'Patrulla'
  | 'Bomberos'
  | 'Defensa Civil';

export interface UnidadEmergenciaData {
  idunidademergencia: number;
  idcliente: number;
  idcondado: number;
  tipopropiedad: TipoPropiedad;
  placa: string;
  capacidad: string | null;
  contactoproveedor: string | null;
  unidademergencia: string;
  tipounidademergencia: TipoUnidadEmergencia;
  activo: boolean;
  latitud: number | null;
  longitud: number | null;
}

export interface ApiEnvelope<T> {
  data: T;
  meta: { pagination: object | null };
}

/** OpenAPI 1.1.0 — idcliente deprecated/ignored (JWT Proveedor). */
export interface UnidadCreateRequest {
  idcondado: number;
  tipopropiedad: TipoPropiedad;
  placa: string;
  capacidad?: string;
  contactoproveedor?: string;
  unidademergencia: string;
  tipounidademergencia: TipoUnidadEmergencia;
  activo?: boolean;
  gmail?: string;
  /** @deprecated Ignorado — se resuelve del JWT */
  idcliente?: number;
}

export interface UnidadCreatedData {
  idunidademergencia: number;
  placa: string;
  activo: boolean;
}

export interface UnidadPatchRequest {
  tipopropiedad?: TipoPropiedad;
  capacidad?: string;
  idcondado?: number;
  contactoproveedor?: string;
  unidademergencia?: string;
  tipounidademergencia?: TipoUnidadEmergencia;
  latitud?: number;
  longitud?: number;
}

export interface UnidadUpdatedData {
  idunidademergencia: number;
  campos_modificados: string[];
}

export interface ImportacionLoteFallida {
  fila: number;
  motivo: string;
}

export interface ImportacionLoteData {
  insertadas: number;
  usuarios_creados?: number;
  fallidas: ImportacionLoteFallida[];
}

export interface BajaUnidadData {
  idunidademergencia: number;
  activo: false;
}
