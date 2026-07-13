export type EstadoAccidente =
  | 'BORRADOR'
  | 'REPORTADO'
  | 'BUSCANDO_UNIDAD'
  | 'ASIGNADO'
  | 'EN_ATENCIÓN'
  | 'CERRADO'
  | 'DESCARTADO'
  | 'FUSIONADO';

export interface AdvertenciaValidacion {
  code: 'fuera_cobertura' | 'duplicado_posible';
  detail: string;
}

export interface EnvelopeMeta {
  pagination: { next_cursor: string | null; limit: number } | null;
}

export interface ApiEnvelope<T> {
  data: T;
  meta: EnvelopeMeta;
}

export interface RegistrarAccidenteRequest {
  latitudinicio: number;
  longitudinicio: number;
  fechahoraaccidente: number;
  registroRetrospectivo?: boolean;
  justificacionRetrospectiva?: string;
  idseveridad: 1 | 2 | 3 | 4;
  descripcion: string;
  idcalle: number;
  codigopostal?: string;
  horainicio?: number;
  numvehiculos?: number;
  numvictimas?: number;
  numheridos?: number;
  numfallecidos?: number;
  distanciamillas?: number;
  duracionminutos?: number;
  idperiododia?: number;
  idestadoclima?: number;
  idelementofisico?: number;
  idtiporeportado?: number;
}

export interface RegistrarAccidenteData {
  message: string;
  idaccidente: string;
  estado: EstadoAccidente;
  advertencias?: AdvertenciaValidacion[];
  fechahoramodificado: number;
}

export interface ConfirmarReporteRequest {
  confirmacion: boolean;
}

export interface ConfirmarReporteData {
  message: string;
  idaccidente: string;
  estado: EstadoAccidente;
}

/** Item de catálogo geográfico (Dim_Pais/Dim_Estado/Dim_Condado/Dim_Ciudad/Dim_Calle). */
export interface CatalogoItem {
  id: number;
  nombre: string;
}

export interface GeocodificacionInversaData {
  idcalle: number | null;
  ubicacion: Record<string, unknown>;
  precision_metros?: number;
  en_cobertura_operativa: boolean;
}

export interface DuplicadoConflictData {
  error: string;
  detail: string;
  code: string;
  idaccidente_similar: string | null;
  idaccidente_principal_sugerido: string | null;
  idaccidente_duplicado_sugerido: string | null;
}

export interface UbicacionLegible {
  idcalle?: number;
  calle?: string | null;
  ciudad?: string | null;
  estado?: string | null;
}

export interface AccidenteListItem {
  idaccidente: string;
  idseveridad: number;
  descripcion: string;
  estado_actual?: EstadoAccidente;
  activo: boolean;
  fechahoraaccidente: number;
  ubicacion?: UbicacionLegible | null;
}

export interface HistorialEstado {
  estado: EstadoAccidente;
  fechahoramodificado: number;
  idusuario: number;
}

export interface AccidenteDetalle extends AccidenteListItem {
  historial_estados: HistorialEstado[];
  ubicacion: UbicacionLegible;
  numvehiculos?: number;
  numheridos?: number;
  numfallecidos?: number;
}

export interface ActualizarAccidenteRequest {
  numvehiculos?: number;
  numvictimas?: number;
  numheridos?: number;
  numfallecidos?: number;
  descripcion?: string;
  confirmacion_campos_criticos?: boolean;
}

export interface ActualizarAccidenteData {
  message: string;
  idaccidente: string;
  campos_modificados: string[];
}

export interface DescartarCasoRequest {
  motivo?: string;
}

export interface DescartarCasoData {
  message: string;
  idaccidente: string;
  estado: EstadoAccidente;
}

export interface FusionarReportesRequest {
  idaccidenteprincipal: string;
  confirmacion: boolean;
}

export interface FusionarReportesData {
  message: string;
  idaccidente_duplicado: string;
  idaccidente_principal: string;
  estado_duplicado: EstadoAccidente;
}

export interface EscalarSeveridadRequest {
  idseveridad: 1 | 2 | 3 | 4;
  numheridos?: number;
  numfallecidos?: number;
  descripcion?: string;
  nota: string;
}

export interface EscalarSeveridadData {
  message: string;
  idaccidente: string;
  idseveridad: number;
  estado: EstadoAccidente;
}
