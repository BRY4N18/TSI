export interface ApiEnvelope<T> {
  data: T;
  meta: Record<string, unknown>;
}

export type EstadoCaso = 'BUSCANDO_UNIDAD' | 'ASIGNADO';
export type EstadoDespacho =
  | 'Pendiente'
  | 'Confirmado'
  | 'Rechazado'
  | 'Timeout'
  | 'Abortado'
  | 'En_sitio'
  | 'Retirado';
export type EstadoNotificacion =
  | 'Pendiente'
  | 'Notificada'
  | 'Confirmada'
  | 'Rechazada'
  | 'No_entregada';
export type OrigenDespacho = 'Automatico' | 'Manual' | 'Escalado_zona';

export interface IntentoDespacho {
  iddespacho: number;
  idunidademergencia: number;
  unidademergencia: string;
  tipounidademergencia?: string;
  estado: EstadoDespacho;
  estadonotificacion?: EstadoNotificacion | null;
  motivo?: string | null;
  origen: OrigenDespacho | string;
  fechahoradespacho: number;
  activo: boolean;
}

export interface EstadoDespachoData {
  idaccidente: string;
  estado_caso: EstadoCaso;
  tiempo_transcurrido_seg: number;
  intentos: IntentoDespacho[];
  unidades_activas: IntentoDespacho[];
  mensaje?: string;
}

export interface UnidadCandidata {
  idunidademergencia: number;
  unidademergencia: string;
  tipounidademergencia: string;
  distancia_km: number;
  puntuacion: number;
  estado_unidad: 'Activa';
  eta_minutos?: number;
}

export interface UnidadesCandidatasData {
  idaccidente: string;
  condado_filtro?: string;
  incluye_vecinos: boolean;
  candidatas: UnidadCandidata[];
}

export interface DespachoCreadoData {
  message: string;
  idaccidente: string;
  iddespacho: number;
  idnotificaciondespacho: number;
  idunidademergencia: number;
  unidademergencia?: string;
  origen: OrigenDespacho | string;
  estado_caso: EstadoCaso;
}

export interface PendienteDespacho {
  idnotificaciondespacho: number;
  idaccidente: string;
  idseveridad: number;
  severidad?: string;
  estadonotificacion: EstadoNotificacion;
  descripcion?: string;
  direccion_aproximada?: string;
  latitud?: number;
  longitud?: number;
  eta_minutos?: number;
  fechahora: number;
}

export interface DetalleDespachoUnidadData extends PendienteDespacho {
  ruta_sugerida_geojson?: Record<string, unknown>;
}

export interface ConfirmarDespachoData {
  message: string;
  idaccidente: string;
  iddespacho: number;
  estado_caso: EstadoCaso;
  estado_unidad: 'Ocupada';
}

export interface RechazarDespachoRequest {
  motivo: string;
}

export interface RechazarDespachoData {
  message: string;
  idaccidente: string;
  iddespacho: number;
  reasignacion_iniciada: boolean;
}

export interface PrioridadSeveridad {
  idseveridad: 1 | 2 | 3 | 4;
  orden_tipos: Array<'Ambulancia' | 'Grua' | 'Patrulla'>;
}

export interface ParametrosDespachoData {
  timeout_respuesta_seg: number;
  peso_distancia_pct: number;
  peso_concordancia_pct: number;
  peso_disponibilidad_pct: number;
  prioridades_por_severidad: PrioridadSeveridad[];
  keywords_severidad_moderada?: string[];
}

export interface ActualizarParametrosRequest {
  timeout_respuesta_seg?: number;
  peso_distancia_pct?: number;
  peso_concordancia_pct?: number;
  peso_disponibilidad_pct?: number;
  prioridades_por_severidad?: PrioridadSeveridad[];
  keywords_severidad_moderada?: string[];
}
