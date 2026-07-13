/** Tipos derivados del contrato seguimiento-cierre-de-casos.openapi.yaml */

export interface EnvelopeMeta {
  timestamp: string;
  request_id?: string;
  pagination?: {
    next_cursor?: string | null;
    limit?: number;
  };
}

export interface ApiEnvelope<T> {
  data: T;
  meta: EnvelopeMeta;
}

export interface Coordenada {
  latitud: number;
  longitud: number;
}

export interface RegistrarPosicionRequest {
  idunidademergencia: number;
  idaccidente: string;
  latitud: number;
  longitud: number;
  fechahora: number;
}

export interface PosicionAceptadaData {
  aceptado: boolean;
  llegada_automatica: boolean;
}

export interface LlegadaRegistradaData {
  iddespacho: number;
  fechahorallegada: number;
  estado_caso: string;
}

export interface MarcadorAccidente {
  idaccidente: string;
  idseveridad: number;
  coordenadas: Coordenada;
  estado: string;
}

export interface UnidadEnMapa {
  idunidademergencia: number;
  unidademergencia: string;
  estado_unidad: string;
  coordenadas: Coordenada;
  idaccidente?: string | null;
  eta_minutos?: number | null;
  distancia_restante_km?: number | null;
}

export interface MapaSeguimientoData {
  accidentes_activos: MarcadorAccidente[];
  unidades: UnidadEnMapa[];
}

export interface PuntoGps {
  latitud: number;
  longitud: number;
  fechahora: number;
}

export interface DespachoSeguimiento {
  iddespacho: number;
  idunidademergencia: number;
  unidademergencia: string;
  estado: string;
  fechahoradespacho: number;
  fechahorallegada?: number | null;
  fechahoraretiro?: number | null;
  eta_minutos?: number | null;
  ruta_recorrida: PuntoGps[];
}

export interface SeguimientoAccidenteData {
  idaccidente: string;
  estado_caso: string;
  coordenadas_accidente: Coordenada;
  despachos: DespachoSeguimiento[];
}

export interface CerrarCasoRequest {
  resultado_atencion: string;
  numvehiculos?: number;
  numvictimas?: number;
  numheridos?: number;
  numfallecidos?: number;
  calificacion?: number;
  observaciones_finales?: string;
}

export interface CierreCasoData {
  idaccidente: string;
  estado_caso: string;
  horafin: number;
  duracionminutos: number;
  tiempos: { duracionminutos: number };
  despachos_retirados: number[];
}

export interface CancelarCasoRequest {
  motivo: string;
}

export interface ForzarRetiroData {
  iddespacho: number;
  fechahoraretiro: number;
  idusuario_operador: string;
  caso_cerrado: boolean;
  estado_caso: string;
}

export interface AbortarMisionRequest {
  motivo?: string;
}

export interface AbortarMisionData {
  iddespacho: number;
  idaccidente: string;
  estado_despacho: string;
  estado_unidad: string;
  reasignacion_disparada: boolean;
}

export interface TiemposCaso {
  respuesta_min: number | null;
  transito_min: number | null;
  atencion_min: number | null;
  duracion_total_min: number | null;
}

export interface HistorialEmergenciaItem {
  idaccidente: string;
  fecha: number;
  estado: string;
  severidad: number;
  ubicacion: string;
  tiempos: TiemposCaso;
  unidad_principal: string | null;
}

export interface HistorialEmergenciasData {
  items: HistorialEmergenciaItem[];
  next_cursor: string | null;
}

export interface ExpedienteData {
  accidente: Record<string, unknown>;
  estado_actual: string;
  historial_estados_caso: unknown[];
  despachos: unknown[];
  notas: unknown[];
  evidencias: unknown[];
  trayectoria_gps: unknown[];
}

export type SeguimientoSseEventType = 'seguimiento.posicion' | 'seguimiento.eta' | 'seguimiento.estado';

export interface SeguimientoSseEvent<T = Record<string, unknown>> {
  type: SeguimientoSseEventType;
  data: T;
}
