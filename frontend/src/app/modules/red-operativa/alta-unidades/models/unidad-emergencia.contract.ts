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
  /**
   * Nombre legible del condado y su estado, resueltos por el backend.
   *
   * Sin ellos la pantalla mostraba "Condado #7" y la exportación a CSV no podía
   * producir un archivo reimportable, porque la importación trabaja con nombres
   * (hallazgo #16). Pueden venir `null` si el catálogo no resuelve el id.
   */
  condado?: string | null;
  estado?: string | null;
  tipopropiedad: TipoPropiedad;
  placa: string;
  capacidad: string | null;
  contactoproveedor: string | null;
  unidademergencia: string;
  tipounidademergencia: TipoUnidadEmergencia;
  idusuario?: number | null;
  /** Nombre y apellidos del usuario de acceso de la unidad. Solo lo devuelve el
   * detalle; es lo que se pinta en pantalla en lugar de `idusuario`. */
  usuario_nombre?: string | null;
  activo: boolean;
  latitud: number | null;
  longitud: number | null;
}

export interface PaginationMeta {
  next_cursor: number | null;
  limit: number;
}

export interface ApiEnvelope<T> {
  data: T;
  meta: { pagination: PaginationMeta | null };
}

/** Query state for GET /unidades (FR-UI-022…025). */
export interface CatalogQueryState {
  cursor?: number | null;
  limit?: number;
  q?: string;
  /** null/undefined = Todas */
  activo?: boolean | null;
  tipounidademergencia?: TipoUnidadEmergencia | '' | null;
}

export interface UnidadesListData {
  items: UnidadEmergenciaData[];
}

export interface UnidadesListPage {
  items: UnidadEmergenciaData[];
  pagination: PaginationMeta;
}

/** OpenAPI 1.2.0 — idcliente deprecated/ignored (JWT Proveedor); gmail opcional (corrección 2026-08-08). */
export interface UnidadCreateRequest {
  idcondado: number;
  tipopropiedad: TipoPropiedad;
  placa: string;
  capacidad?: string;
  contactoproveedor?: string;
  unidademergencia: string;
  tipounidademergencia: TipoUnidadEmergencia;
  activo?: boolean;
  /** Opcional: si se envía, crea login Unidad + liga idusuario (CU-O30). Sin él, la unidad queda sin acceso hasta que se le asigne login después. */
  gmail?: string;
  /** @deprecated Ignorado — se resuelve del JWT */
  idcliente?: number;
}

export interface UnidadCreatedData {
  idunidademergencia: number;
  placa: string;
  activo: boolean;
  idusuario?: number;
  usuario_creado?: boolean;
  invitacion_enviada: boolean;
  invitacion_error?: string;
}

export interface UnidadInvitacionReenvioData {
  idunidademergencia: number;
  idusuario: number;
  invitacion_enviada: boolean;
  invitacion_error?: string;
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
