export type TipoCliente = 'Proveedor' | 'Aseguradora' | 'Municipio' | 'Smart City';
export type EstadoCuenta =
  | 'Pendiente_Aprobación'
  | 'Activo'
  | 'Rechazado'
  | 'Rechazado_Anulado'
  | 'Dado de baja';
export type EstadoOnboarding = 'Pendiente' | 'En progreso' | 'Completado';
export type EtapaOnboarding = 'cambio_password' | 'perfil_corporativo' | 'preferencias';

export interface ApiEnvelope<T> {
  data: T;
  meta: { pagination: object | null };
}

export interface AdminLocalInput {
  nombres: string;
  apellidos: string;
  gmail: string;
}

export interface AutorregistroProveedorRequest {
  razon_social: string;
  nombre: string;
  tipo: TipoCliente;
  nit_identificacion: string;
  fecha_inicio_contrato?: number | null;
  admin_local: AdminLocalInput;
}

export interface AutorregistroProveedorData {
  idcliente: number;
  estado: 'Pendiente_Aprobación';
  admin_local_id: number;
  admin_local_gmail: string;
  message?: string;
}

export interface SolicitudItem {
  idcliente: number;
  razon_social: string;
  nit_identificacion: string;
  tipo: TipoCliente;
  estado: 'Pendiente_Aprobación' | 'Rechazado';
}

export interface AprobacionRequest {
  decision: 'aprobar' | 'rechazar';
  motivo?: string;
}

export interface AprobacionData {
  idcliente: number;
  estado: 'Activo' | 'Rechazado' | 'Rechazado_Anulado';
  estado_onboarding?: EstadoOnboarding | null;
  message?: string;
}

/** @deprecated CU-O01 legado — no usar para Proveedor */
export interface RegistroCuentaRequest {
  razon_social: string;
  nombre: string;
  tipo: TipoCliente;
  nit_identificacion: string;
  fecha_inicio_contrato: number;
  admin_local: AdminLocalInput;
}

/** @deprecated CU-O01 legado */
export interface RegistroCuentaData {
  idcliente: number;
  estado: 'Activo';
  admin_local_id: number;
  admin_local_gmail: string;
  message?: string;
}

/** @deprecated CU-O12 — logo lo pone el cliente en onboarding */
export interface ConfiguracionCuentaRequest {
  plan_suscripcion: string;
  logo_url?: string;
}

export interface ConfiguracionCuentaData {
  idcliente: number;
  plan_suscripcion: string;
  logo_url: string | null;
  estado_onboarding: EstadoOnboarding;
}

export interface OnboardingProgresoData {
  idcliente: number;
  estado_onboarding: EstadoOnboarding;
  etapas_completadas: EtapaOnboarding[];
  etapa_actual: EtapaOnboarding | null;
}

export interface DatosEtapaPerfil {
  razon_social?: string;
  nombre?: string;
  logo_url?: string;
}

export interface DatosEtapaPreferencias {
  umbrales_alerta?: string;
  canales_notificacion?: 'email' | 'sms' | 'ambos';
  telefono_sms?: string;
  zonas_geograficas?: string;
  destinatarios_reportes?: string;
  frecuencia_reportes?: string;
  formato_reportes?: string;
}

export interface CompletarEtapaRequest {
  etapa: EtapaOnboarding;
  datos_etapa?: DatosEtapaPerfil | DatosEtapaPreferencias;
}

export interface CompletarEtapaData {
  etapa: EtapaOnboarding;
  progreso: OnboardingProgresoData;
}

export interface ReenviarInvitacionRequest {
  id_usuario?: number;
}

export interface ReenviarInvitacionData {
  message: string;
  id_usuario: number;
}

export interface LogoUploadUrlData {
  upload_url: string;
  logo_url: string;
  expires_at: string;
}
