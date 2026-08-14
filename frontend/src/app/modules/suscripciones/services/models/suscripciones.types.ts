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
export type PeriodicidadPlan = 'Mensual' | 'Anual';
/**
 * Severidad atendible por un plan: el `idseveridad` de `Dim_Severidad`.
 * Hasta 2026-08-11 era una escala paralela de nombres ('Baja'|'Media'|'Alta')
 * que no correspondía a ninguna fila del catálogo real.
 */
export type SeveridadPlan = number;

/** Fila del catálogo `Dim_Severidad` que alimenta el selector del formulario. */
export interface SeveridadCatalogo {
  idseveridad: number;
  severidad: string;
  descripcion?: string | null;
}
export type TipoMetodoPago = 'tarjeta' | 'transferencia' | 'paypal';
export type EstadoSolicitudCambioPlan = 'Pendiente' | 'Aprobada' | 'Rechazada';
// 'En disputa' faltaba: el backend ya podia dejar la factura en ese estado
// (RF-APM-014) y el frontend no lo conocia, asi que se pintaba como estado
// desconocido y nada explicaba por que el cobro se habia detenido.
export type EstadoPagoFactura = 'Pendiente' | 'Pagada' | 'Fallida' | 'En disputa';

export interface AltaSuscripcionRequest {
  idplan: number;
  renovacionautomatica?: boolean;
}

export interface Suscripcion {
  id_suscripcion?: number;
  idcliente?: number;
  idplan?: number;
  precio?: number;
  periodicidad?: PeriodicidadPlan;
  nivel?: NivelPlan;
  severidades_desbloqueadas?: SeveridadPlan[];
  carga_lote_habilitada?: boolean;
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
  /**
   * Reducción de plan ya aprobada que aplica al cierre del ciclo (decisión #27).
   * Ausente si no hay ningún cambio programado.
   */
  plan_programado_nombre?: string | null;
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
  /** Epoch en milisegundos: la columna de Pinot es LONG, no texto `MM/AA`. */
  fechaexpiracion?: number | string | null;
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
  /**
   * Límite de llamadas por minuto (RN-SUSF-019, añadido 2026-08-08).
   * No es un prorrateo del mensual: protege contra ráfagas. Lo exige el SRS
   * §3.4.1 y es el origen de `Dim_Partner.limitellamadasminuto` (RF-PON-003).
   */
  api_calls_minuto: number;
}

export interface PlanRequest {
  nombre: string;
  precio: number;
  /** Precio unitario de cada llamada que supera el cupo (RF-O54.1). Distinto de `precio`, que es la suscripción. */
  precio_excedente_llamada: number;
  limites: PlanLimites;
  nivel: NivelPlan;
  periodicidad: PeriodicidadPlan;
  severidades_desbloqueadas: SeveridadPlan[];
  /** Habilita CU-O40 (carga en lote de unidades) para proveedores en este plan. Opcional, default false. */
  carga_lote_habilitada?: boolean;
}

export interface PlanPatchRequest {
  nombre?: string;
  precio?: number;
  /** Precio unitario de cada llamada que supera el cupo (RF-O54.1). Distinto de `precio`, que es la suscripción. */
  precio_excedente_llamada?: number;
  limites?: PlanLimites;
  nivel?: NivelPlan;
  periodicidad?: PeriodicidadPlan;
  severidades_desbloqueadas?: SeveridadPlan[];
  carga_lote_habilitada?: boolean;
  activo?: boolean;
}

export interface Plan {
  idplan?: number;
  nombre?: string;
  precio?: number;
  /** Precio unitario de cada llamada que supera el cupo (RF-O54.1). Distinto de `precio`, que es la suscripción. */
  precio_excedente_llamada?: number;
  limites?: PlanLimites;
  nivel?: NivelPlan;
  periodicidad?: PeriodicidadPlan;
  severidades_desbloqueadas?: SeveridadPlan[];
  carga_lote_habilitada?: boolean;
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
