/**
 * Proyección hacia la UI de los esquemas cerrados en el contrato OpenAPI del
 * backend. Si algo aquí contradice ese contrato, manda el contrato.
 *
 * OJO CON LOS CENTINELAS: Pinot no almacena NULL en este proyecto, así que la
 * ausencia de valor llega como un centinela (`''`, `-1`, `0`, año 9999) y
 * cruza hasta aquí. Nunca se renderizan crudos — ver `centinelas.ts`.
 */

/** Estado derivado por el backend (§ 9). La UI lo presenta; jamás lo edita. */
export type EstadoPartner =
  | 'Registrado'
  | 'Plan asignado'
  | 'Pruebas activo'
  | 'Pendiente de aprobación'
  | 'Producción activa'
  | 'Suspendido';

/** El acento de 'Producción' es parte del valor, no una etiqueta de UI. */
export type Entorno = 'Sandbox' | 'Producción';

export type EstadoVersion = 'vigente' | 'soportada' | 'retirada';

export interface PartnerListItem {
  idpartner: number;
  idcliente: number;
  nombrepartner: string;
  /** `''` = sin plan (centinela, NO null). */
  planapi: string;
  /** `-1` = sin cupo asignado. */
  limitellamadasmes: number;
  /** `-1` = sin cupo asignado. */
  limitellamadasminuto: number;
  activo: boolean;
  estado: EstadoPartner;
}

export interface EventoHistorial {
  idhistorial: number;
  idpartner: number;
  idcredencial: number;
  tipo_cambio: string;
  ejecutado_por: string;
  motivo: string;
  estado_anterior: string;
  estado_nuevo: string;
  fecha_cambio: number;
}

export interface CredencialItem {
  idcredencial: number;
  nombre_credencial: string;
  entorno: Entorno;
  activo: boolean;
  /** epoch ms */
  fecha_creacion: number;
  /** epoch ms; `NUNCA_EXPIRA` (año 9999) = no expira. */
  fecha_expiracion: number;
}

export interface PartnerDetalle extends PartnerListItem {
  contacto_tecnico_nombre: string;
  contacto_tecnico_gmail: string;
  /** `''` = sin suspensión. */
  fecha_suspension: string;
  /** `''` = sin suspensión. */
  motivo_suspension: string;
  credenciales: CredencialItem[];
  historial: EventoHistorial[];
}

/**
 * ÚNICA forma en que el secreto en claro entra al frontend. No se persiste
 * jamás: vive en memoria del componente hasta que el usuario confirma que lo
 * guardó (RN-PON-005, FR-UI-020/021).
 */
export interface CredencialEmitida extends CredencialItem {
  client_id: string;
  client_secret: string;
}

export interface VersionContrato {
  idversion: number;
  id_servicio: number;
  version: string;
  estado: EstadoVersion;
  /** `''` = sin documento publicado. */
  spec_url: string;
  fecha_publicacion: number;
  /** `0` = sin retiro planificado (centinela). */
  fecha_retiro: number;
}

export interface ContratoIntegracion extends VersionContrato {
  versiones: VersionContrato[];
}

export interface RegistrarPartnerRequest {
  idcliente: number;
  nombrepartner: string;
  contacto_tecnico_nombre: string;
  contacto_tecnico_gmail: string;
}

export interface EmitirCredencialRequest {
  nombre_credencial: string;
  entorno?: Entorno;
}

export type DecisionPromocion = 'aprobar' | 'rechazar';

export interface ResolucionPromocionRequest {
  decision: DecisionPromocion;
  motivo?: string;
}

export interface ResolucionPromocionData {
  idpartner: number;
  estado: EstadoPartner;
  motivo?: string;
}
