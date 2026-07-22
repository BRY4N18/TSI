export interface ApiEnvelope<T> {
  data: T;
  meta: Record<string, unknown>;
}

export type EstadoTicket =
  | 'Abierto'
  | 'Pendiente_de_clasificacion'
  | 'En_progreso'
  | 'Escalado'
  | 'Resuelto'
  | 'Cerrado'
  | 'Reabierto';

export type SlaStatus = 'en curso' | 'en riesgo' | 'incumplido' | 'cumplido' | null;

export interface Ticket {
  id_reclamo: number;
  idcliente: number;
  asunto: string;
  descripcion: string;
  tipo: string;
  tipo_incidencia?: string | null;
  prioridad?: string | null;
  estado: EstadoTicket;
  sla_status: SlaStatus;
  sla_primera_respuesta?: number | null;
  sla_resolucion?: number | null;
  id_agente_asignado?: number | null;
  cierreconfirmadocliente: boolean;
  fechahora: number;
}

export interface HistorialTicketItem {
  id_historial: number;
  id_reclamo: number;
  tipo_accion: string;
  mensaje?: string | null;
  es_nota_interna: boolean;
  idusuario?: number | null;
  estado_anterior?: string | null;
  estado_nuevo?: string | null;
  fecha_accion: number;
}

export interface TicketDetalleData {
  ticket: Ticket;
  historial: HistorialTicketItem[];
}

export interface TransicionTicketData {
  id_reclamo: number;
  estado_anterior: string;
  estado_nuevo: string;
  agente_asignado?: number | null;
}

export interface RegistrarTicketRequest {
  idcliente: number;
  asunto: string;
  descripcion: string;
  tipo: string;
  idaccidente?: string;
}

export interface SLAConfig {
  idslaconfig: number;
  idplan: number;
  tipoincidencia: string;
  prioridad: string;
  activo: boolean;
  tiemporespuestamax: number;
  tiemporesolucionmax: number;
  fechavigenciadesde: number;
  fechavigenciahasta: number | null;
}

export interface CrearSLAConfigRequest {
  idplan: number;
  tipoincidencia: string;
  prioridad: string;
  tiemporespuestamax: number;
  tiemporesolucionmax: number;
}

export interface DashboardSoporteData {
  total_tickets: number;
  por_estado: Record<string, number>;
  por_prioridad: Record<string, number>;
  por_tipo_incidencia: Record<string, number>;
  por_cliente: Record<string, number>;
  sla_en_riesgo: number;
  sla_vencidos: number;
  tiempo_promedio_primera_respuesta_ms: number | null;
  tiempo_promedio_resolucion_ms: number | null;
  tasa_reapertura: number;
}
