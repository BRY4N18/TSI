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
  /** Grant de un solo canje para abrir la demo (RF-CPP-001 -> RF-NV-001); solo presente en la respuesta de registro. */
  demo_grant?: string;
}

/** Fila de `Fact_Pipeline` — un cambio de etapa. */
export interface TransicionPipeline {
  id_transicion: number;
  id_prospecto: number;
  etapa_anterior: string | null;
  etapa_nueva: string;
  notas?: string | null;
  motivo_perdida?: string | null;
  gerente_id?: number | null;
  fecha_transicion?: number;
}

/** Fila de `Fact_Asignacion` — un cambio de dueño comercial. */
export interface AsignacionProspecto {
  idasignacion: number;
  idprospecto: number;
  idusuariogerenteanterior?: number | null;
  idusuariogerenteactual: number;
  tipoasignacion: string;
  motivo?: string | null;
  fechahoraasignacion?: number;
}

/**
 * Detalle del prospecto: sus campos **más su rastro**.
 *
 * `GET /prospectos/{id}` ya devolvía ambos historiales (RF-CPP-008: "historial
 * de `Fact_Pipeline` y `Fact_Asignacion` incluido") y la pantalla los tiraba a
 * la basura, así que no había forma de ver quién tuvo el prospecto ni por qué
 * etapas pasó (hallazgo #14).
 */
export interface ProspectoDetalle extends Prospecto {
  historial_pipeline?: TransicionPipeline[];
  historial_asignacion?: AsignacionProspecto[];
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
  /**
   * Dueño que el cliente cree vigente — control de concurrencia optimista.
   *
   * ⚠️ **Obligatorio en la práctica.** El backend compara
   * `data.get("idusuario_esperado") != owner` y responde `409` si no coincide;
   * omitirlo hace que compare `undefined` contra el dueño real, así que
   * **cualquier** prospecto ya asignado rechazaba la reasignación. Era opcional
   * en el tipo y la pantalla no lo enviaba (hallazgo #14).
   */
  idusuario_esperado: number | null;
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
  /** Requerido: sin esto la cuenta queda sin nadie que pueda iniciar sesión (CU-O96). */
  admin_local: {
    nombres: string;
    apellidos: string;
    gmail: string;
  };
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

/**
 * Nombres de `Dim_Severidad` que el catálogo público devuelve ya resueltos.
 *
 * ⚠️ Eran `'Baja' | 'Media' | 'Alta'`, vocabulario anterior a la migración del
 * 2026-08-11 (`database/migra_severidades_plan_a_idseveridad.py`), que pasó los
 * planes a los ids de `Dim_Severidad`. El backend resuelve esos ids a
 * `Leve | Moderado | Grave | Fatal`, así que el tipo del cliente **nunca**
 * coincidía con el dato real: el badge de color caía siempre al caso por
 * defecto y hasta "Fatal" se pintaba en verde en la página de ventas
 * (hallazgo #2).
 */
export type SeveridadPlan = 'Leve' | 'Moderado' | 'Grave' | 'Fatal';

export interface PlanPublico {
  idplan: number;
  nombre: string;
  precio: number;
  limites: string;
  nivel: string;
  periodicidad?: 'Mensual' | 'Anual';
  severidades_desbloqueadas: SeveridadPlan[];
  /** Opcional: si la API/Dim_Plan lo expone; si no, UI marca Profesional como destacado. */
  destacado?: boolean;
}
