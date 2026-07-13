export type TipoCliente = 'Aseguradora' | 'Municipio' | 'Smart City';
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

export interface RegistroCuentaRequest {
  razon_social: string;
  nombre: string;
  tipo: TipoCliente;
  nit_identificacion: string;
  fecha_inicio_contrato: number;
  admin_local: AdminLocalInput;
}

export interface RegistroCuentaData {
  idcliente: number;
  estado: 'Activo';
  admin_local_id: number;
  admin_local_gmail: string;
  message?: string;
}

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
