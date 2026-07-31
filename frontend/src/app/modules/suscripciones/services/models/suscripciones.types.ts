export interface ApiEnvelope<T> {
  data: T;
  meta?: Record<string, unknown> & PaginationMetaFields;
}

export interface PaginationMetaFields {
  pagination?: {
    next_cursor?: number | string | null;
    limit?: number;
  };
  regularizacion_disparada?: boolean;
}

export type EstadoSuscripcion = 'Activa' | 'Suspendida' | 'Cancelada';
export type NivelPlan = 'Básico' | 'Profesional' | 'Empresarial';
export type TipoMetodoPago = 'tarjeta' | 'transferencia' | 'paypal';
export type EstadoSolicitudCambioPlan = 'Pendiente' | 'Aprobada' | 'Rechazada';
export type EstadoPagoFactura = 'Pendiente' | 'Pagada' | 'Fallida';

export interface AltaSuscripcionRequest {
  idplan: number;
  renovacionautomatica?: boolean;
}

export interface Suscripcion {
  id_suscripcion?: number;
  idcliente?: number;
  idplan?: number;
  precio?: number;
  estado?: EstadoSuscripcion;
  activo?: boolean;
  renovacionautomatica?: boolean;
  fecha_inicio?: string;
  fecha_fin?: string;
  motivocancelacion?: string | null;
  fechacancelacion?: string | null;
}

export interface SuscripcionDetalle extends Suscripcion {
  acceso_permitido?: boolean;
  plan_nombre?: string;
  nivel?: NivelPlan;
}

export type SuscripcionEnvelope = ApiEnvelope<Suscripcion>;
export type SuscripcionDetalleEnvelope = ApiEnvelope<SuscripcionDetalle>;

export interface CancelarSuscripcionRequest {
  motivocancelacion: string;
}

export interface MetodoPagoRequest {
  tipo: TipoMetodoPago;
  datos_pasarela: Record<string, unknown>;
}

export interface MetodoPago {
  idmetodopago?: number;
  idcliente?: number;
  tipo?: string;
  ultimosdigitos?: string;
  fechaexpiracion?: string | null;
  activo?: boolean;
}

export type MetodoPagoEnvelope = ApiEnvelope<MetodoPago>;
export type MetodoPagoListEnvelope = ApiEnvelope<MetodoPago[]>;

export interface SolicitudCambioPlanRequest {
  idplansolicitado: number;
  motivo: string;
}

export interface SolicitudCambioPlan {
  idsolicitud?: number;
  idcliente?: number;
  idplanactual?: number;
  idplansolicitado?: number;
  estado?: EstadoSolicitudCambioPlan;
  motivo?: string;
  motivo_rechazo?: string | null;
  idadminaprobador?: number | null;
  fecha_solicitud?: string;
  fecha_resolucion?: string | null;
}

export type SolicitudEnvelope = ApiEnvelope<SolicitudCambioPlan>;
export type SolicitudListEnvelope = ApiEnvelope<SolicitudCambioPlan[]>;

export interface RechazarCambioPlanRequest {
  motivo_rechazo: string;
}

export interface PlanLimites {
  unidades_max: number;
  usuarios_max: number;
  api_calls_mes: number;
}

export interface PlanRequest {
  nombre: string;
  precio: number;
  limites: PlanLimites;
  nivel: NivelPlan;
}

export interface PlanPatchRequest {
  nombre?: string;
  precio?: number;
  limites?: PlanLimites;
  nivel?: NivelPlan;
  activo?: boolean;
}

export interface Plan {
  idplan?: number;
  nombre?: string;
  precio?: number;
  limites?: PlanLimites;
  nivel?: NivelPlan;
  activo?: boolean;
}

/** Query params for GET /suscripciones/planes (RF-SUSF-001 listado). */
export interface PlanListQuery {
  cursor?: number | null;
  limit?: number;
  q?: string;
  activo?: boolean;
  nivel?: NivelPlan;
  /** @deprecated prefer `activo` */
  solo_activos?: boolean;
}

export type PlanEnvelope = ApiEnvelope<Plan>;
export type PlanListEnvelope = ApiEnvelope<Plan[]>;

export interface FacturaCargo {
  concepto?: string;
  monto?: number;
}

export interface Factura {
  id_factura?: string;
  id_cliente?: number;
  id_suscripcion?: number;
  idmetodopago?: number | null;
  numero_factura?: string;
  periodo?: string;
  estado_pago?: EstadoPagoFactura;
  monto_base?: number;
  impuestos?: number;
  monto_total?: number;
  desglose_cargos?: FacturaCargo[];
  fecha_emision?: string;
  fecha_vencimiento?: string;
  reintentos?: number;
  resultado_ultimo_reintento?: string | null;
  metodo_ultimosdigitos?: string | null;
}

export type FacturaEnvelope = ApiEnvelope<Factura>;
export type FacturaListEnvelope = ApiEnvelope<Factura[]>;

export interface RegularizacionResult {
  estado_pago?: 'Pagada' | 'Fallida' | 'Pendiente';
  estado_suscripcion?: 'Activa' | 'Suspendida';
  resultado_ultimo_reintento?: string;
}

export type RegularizacionEnvelope = ApiEnvelope<RegularizacionResult>;
