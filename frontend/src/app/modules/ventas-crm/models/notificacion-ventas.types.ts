export type CanalNotificacion = 'email' | 'slack' | 'push';
export type TipoEventoDemo = 'click' | 'tiempo_seccion' | 'inicio_sesion' | 'fin_sesion';
export type ReglaDisparada = 'tiempo_seccion_precios_5min' | 'visito_pricing_3x';

/** Query params usados para pasar el grant de demo desde /registro a /demo (SRS §3.1.2 — continuación natural del registro). */
export const DEMO_QUERY_PARAM_IDPROSPECTO = 'idprospecto';
export const DEMO_QUERY_PARAM_GRANT = 'grant';

export interface ApiEnvelope<T> {
  data: T;
  meta?: {
    pagination?: { next_cursor?: string | null; limit?: number };
  };
}

export interface AbrirSesionDemoRequest {
  idprospecto: number;
  demo_grant: string;
}

export interface SesionDemo {
  idprospecto: number;
  demo_session_token: string;
  demo_expiracion: string;
  modo: 'primer_canje' | 'resume';
}

export interface InteraccionDemoRequest {
  idprospecto: number;
  tipo_evento: TipoEventoDemo;
  seccion: string;
  metadata?: Record<string, unknown>;
  timestamp_evento: number;
}

export interface InteraccionDemo {
  idinteraccion: number;
  idprospecto: number;
  tipo_evento: TipoEventoDemo;
  seccion: string;
  metadata: string;
  timestamp_evento: number;
}

export interface NotificacionVentas {
  idnotificacion: number;
  id_prospecto: number;
  idinteraccion: number;
  idusuariogerentenotificado: number;
  regladisparada: ReglaDisparada;
  canal: CanalNotificacion;
  fechahoranotificacion: number;
}
