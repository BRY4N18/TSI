export interface ApiEnvelope<T> {
  data: T;
  meta?: {
    pagination?: {
      next_cursor?: string | number | null;
      limit?: number;
    };
  };
}

export type TipoOrganizacion = 'Público' | 'Privado';
export type EtapaPipeline =
  | 'Nuevo'
  | 'Contactado'
  | 'Calificado'
  | 'Propuesta'
  | 'Negociación'
  | 'Ganado'
  | 'Perdido';
export type TipoCliente = 'Proveedor' | 'Aseguradora' | 'Municipio' | 'Smart City';

/** Query params for GET /ventas-crm/prospectos (RF-CPP-008). */
export interface ProspectoListQuery {
  cursor?: string | number | null;
  limit?: number;
  activo?: boolean;
  etapa_actual?: EtapaPipeline;
}

export interface Prospecto {
  idprospecto: number;
  nombres: string;
  apellidos: string;
  gmail: string;
  empresa: string;
  tipo_organizacion: TipoOrganizacion;
  cargo: string;
  telefono: string;
  como_nos_conocio: string;
  etapa_actual: EtapaPipeline;
  idusuario: number | null;
  activo: boolean;
  motivo_inactividad: 'perdido' | 'convertido' | null;
  valor_estimado?: number | null;
  fecha_registro?: number;
  asignacion_automatica?: {
    ok: boolean;
    idusuariogerenteactual?: number | null;
    error?: string | null;
  } | null;
}

export interface RegistroProspectoRequest {
  nombres: string;
  apellidos: string;
  gmail: string;
  empresa: string;
  tipo_organizacion: TipoOrganizacion;
  cargo: string;
  telefono: string;
  como_nos_conocio: string;
  valor_estimado?: number | null;
}

export interface AsignacionManualRequest {
  idusuariogerenteactual: number;
  motivo: string;
  idusuario_esperado?: number | null;
}

export interface PipelineTransicionRequest {
  etapa_nueva: 'Contactado' | 'Calificado' | 'Propuesta' | 'Negociación' | 'Perdido';
  etapa_actual_esperada: EtapaPipeline;
  notas?: string | null;
  motivo_perdida?: string | null;
}

export interface ConversionRequest {
  tipo: TipoCliente;
  nit_identificacion: string;
  etapa_actual_esperada: 'Negociación';
}

export interface EntradaDirectaRequest {
  nombre: string;
  razon_social: string;
  tipo: TipoCliente;
  nit_identificacion: string;
}

export interface Cliente {
  idcliente: number;
  idprospecto: number | null;
  nombre: string;
  razon_social: string;
  tipo: TipoCliente;
  nit_identificacion: string;
  estado: string;
  estado_onboarding: string;
  fecha_inicio_contrato?: number;
}

export type SeveridadPlan = 'Baja' | 'Media' | 'Alta';

export interface PlanPublico {
  idplan: number;
  nombre: string;
  precio: number;
  limites: string;
  nivel: string;
  severidades_desbloqueadas: SeveridadPlan[];
  /** Opcional: si la API/Dim_Plan lo expone; si no, UI marca Profesional como destacado. */
  destacado?: boolean;
}
