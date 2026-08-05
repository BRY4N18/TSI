export interface ApiEnvelope<T> {
  data: T;
  meta: Record<string, unknown>;
}

export interface PeriodoParams {
  desde: string;
  hasta: string;
  granularidad?: 'dia' | 'semana' | 'mes';
}

// --- Registro (7) ---
export interface VolumenCasosItem {
  periodo: string;
  total_casos: number;
}
export interface DistribucionSeveridadItem {
  idseveridad: number;
  total_casos: number;
}
export interface DistribucionZonaItem {
  idcalle: number;
  calle_nombre: string | null;
  total_casos: number;
}
export interface CompletitudItem {
  periodo: string;
  pct_completos: number;
}
export interface DescarteFusionItem {
  periodo: string;
  pct_descarte: number;
  pct_fusion: number;
}
export interface RankingUbicacionItem {
  idcalle: number;
  calle_nombre: string | null;
  total_casos: number;
}
export interface ImpactoHumanoItem {
  idcalle: number;
  calle_nombre: string | null;
  total_victimas: number;
  total_heridos: number;
  total_fallecidos: number;
}

// --- Despacho (6) ---
export interface AsignacionOrigenItem {
  idorigendespacho: number;
  origen_nombre: string | null;
  pct_total: number;
}
export interface TiempoReportadoConfirmado {
  promedio_segundos: number;
}
export interface TiempoRespuestaSeveridadItem {
  idseveridad: number;
  promedio_segundos: number;
}
export interface RechazoTimeoutItem {
  idunidademergencia: number;
  unidad_nombre: string | null;
  unidad_placa: string | null;
  pct_rechazo_timeout: number;
}
export interface CargaUnidadItem {
  idunidademergencia: number;
  unidad_nombre: string | null;
  unidad_placa: string | null;
  total_despachos: number;
}
export interface RatioDemandaCapacidadItem {
  idcondado: number;
  condado_nombre: string | null;
  total_accidentes: number;
  unidades_activas: number;
  ratio: number | null;
}

// --- Seguimiento (3) ---
export interface TiempoAsignadoCerradoItem {
  idunidademergencia: number;
  unidad_nombre: string | null;
  unidad_placa: string | null;
  promedio_segundos: number;
}
export interface CierresForzadosItem {
  periodo: string;
  pct_cierres_forzados: number;
}
export interface AbortosPerdidasItem {
  idunidademergencia: number;
  unidad_nombre: string | null;
  unidad_placa: string | null;
  pct_abortos_perdidas: number;
}

// --- Compuestos (3, batch vía Airflow + ClickHouse, solo rol Administrador) ---
export interface ApiEnvelopeCompuesto<T> {
  data: T | null;
  meta: {
    periodo: { desde: string; hasta: string };
    materializado: boolean;
    ultima_corrida: string | null;
  };
}

export interface PerdidaSenalItem {
  idunidademergencia: number;
  unidad_nombre: string | null;
  unidad_placa: string | null;
  idaccidente: number;
  inicio_hueco: string;
  fin_hueco: string;
  duracion_seg: number;
  umbral_usado_seg: number;
}

export interface IndiceCalidadItem {
  periodo: string;
  pct_completitud: number;
  pct_descarte: number;
  pct_fusion: number;
  pct_cobertura_evidencia: number;
  indice_consolidado: number;
}

export interface RendimientoProveedorItem {
  idcliente: number;
  proveedor_nombre: string | null;
  pct_rechazo: number;
  tiempo_llegada_promedio_seg: number;
  pct_abortos: number;
  total_despachos: number;
}
