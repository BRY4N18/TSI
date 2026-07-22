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

export interface UnidadCreateRequest {
  idcliente: number;
  idcondado: number;
  tipopropiedad: TipoPropiedad;
  placa: string;
  capacidad?: string;
  contactoproveedor?: string;
  unidademergencia: string;
  tipounidademergencia: TipoUnidadEmergencia;
  activo?: boolean;
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
  fallidas: ImportacionLoteFallida[];
}

export interface BajaUnidadData {
  idunidademergencia: number;
  activo: false;
}

export interface DisponibilidadData {
  idunidademergencia: number;
  estadonuevo: string;
}

export type EstadoDisponibilidad = 'Activa' | 'Ocupada' | 'Fuera de servicio';
