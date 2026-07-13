export interface PerfilData {
  idcliente: number;
  razon_social: string;
  nombre: string;
  tipo: string;
  nit_identificacion: string;
  logo_url: string | null;
  estado: 'Activo' | 'Dado de baja';
  admin_local_id: number;
}

export interface PreferenciasData {
  id_preferencia: number;
  id_cliente: number;
  umbrales_alerta: string;
  canales_notificacion: 'email' | 'sms' | 'ambos';
  telefono_sms: string | null;
  zonas_geograficas: string;
  destinatarios_reportes: string;
  frecuencia_reportes: string;
  formato_reportes: string;
}

export interface ApiEnvelope<T> {
  data: T;
  meta: { pagination: object | null };
}

export interface PerfilUpdatedData {
  message: string;
  campos_modificados: string[];
  perfil: PerfilData;
}

export interface PreferenciasUpdatedData {
  message: string;
  preferencias: PreferenciasData;
}

export interface LogoUploadUrlData {
  upload_url: string;
  logo_url: string;
  expires_at: string;
}

export interface UsuarioElegible {
  idusuario: number;
  gmail: string;
  nombres: string;
  apellidos: string;
  activo: boolean;
  es_admin_local_actual: boolean;
}

export interface TransferenciaPropiedadData {
  message: string;
  nuevo_admin_local_id: number;
  nombre: string;
  admin_local_anterior_id: number;
}

export interface BajaCuentaData {
  message: string;
  estado: 'Dado de baja';
  sesiones_expulsadas: number;
}
