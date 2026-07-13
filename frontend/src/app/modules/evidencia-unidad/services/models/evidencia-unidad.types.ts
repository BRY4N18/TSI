export type EstadoDisponibilidadUnidad = 'Activa' | 'Ocupada' | 'Fuera de servicio';

export type TipoNotaCampo =
  | 'Observación general'
  | 'Declaración de testigo'
  | 'Daños materiales'
  | 'Condiciones del sitio';

export interface EnvelopeMeta {
  pagination: { next_cursor: string | null; limit: number } | null;
}

export interface ApiEnvelope<T> {
  data: T;
  meta: EnvelopeMeta;
}

export interface AutorEvidencia {
  idusuario: number;
  nombre: string;
}

export interface EvidenciaFotoItem {
  tipo: 'foto';
  idevidenciafoto: number;
  idaccidente: string;
  urlevidenciafoto: string;
  sincronizado: true;
  fechahora: number;
  autor: AutorEvidencia;
}

export interface EvidenciaNotaItem {
  tipo_evidencia: 'nota';
  idnotaaccidentes: number;
  idaccidente: string;
  nota: string;
  tipo: TipoNotaCampo;
  sincronizado: true;
  fechahora: number;
  autor: AutorEvidencia;
}

export interface EvidenciaFotoPendienteItem {
  tipo: 'foto';
  local_id: string;
  idaccidente: string;
  urlevidenciafoto: string;
  sincronizado: false;
  fechahora: number;
  autor?: AutorEvidencia;
}

export interface EvidenciaNotaPendienteItem {
  tipo_evidencia: 'nota';
  local_id: string;
  idaccidente: string;
  nota: string;
  tipo: TipoNotaCampo;
  sincronizado: false;
  fechahora: number;
  autor?: AutorEvidencia;
}

export type EvidenciaItem =
  | EvidenciaFotoItem
  | EvidenciaNotaItem
  | EvidenciaFotoPendienteItem
  | EvidenciaNotaPendienteItem;

export interface EvidenciaListData {
  items: (EvidenciaFotoItem | EvidenciaNotaItem)[];
}

export interface EvidenciaFotoData {
  idevidenciafoto: number;
  idaccidente: string;
  urlevidenciafoto: string;
  sincronizado: true;
  fechahora: number;
}

export interface EvidenciaNotaData {
  idnotaaccidentes: number;
  idaccidente: string;
  nota: string;
  tipo: TipoNotaCampo;
  sincronizado: true;
  fechahora: number;
}

export interface RegistrarNotaCampoRequest {
  nota: string;
  tipo: TipoNotaCampo;
  fechahora?: number;
}

export interface SincronizarNotaPendiente {
  local_id: string;
  nota: string;
  tipo: TipoNotaCampo;
  fechahora: number;
}

export interface SincronizarFotoMetadata {
  local_id: string;
  fechahora: number;
}

export interface SincronizarEvidenciaResultado {
  local_id: string;
  sincronizado: boolean;
  idevidenciafoto: number | null;
  idnotaaccidentes: number | null;
  urlevidenciafoto: string | null;
  error: string | null;
}

export interface SincronizarEvidenciaData {
  sincronizados: number;
  pendientes: number;
  resultados: SincronizarEvidenciaResultado[];
}

export interface DisponibilidadUnidadData {
  idunidademergencia: number;
  estado_actual: EstadoDisponibilidadUnidad;
  incluido_en_despacho: boolean;
  fechahora_ultimo_cambio: number | null;
}

export interface HistorialEstadoUnidadData {
  idhistorialestadosunidadesemergencias: number;
  idunidademergencia: number;
  estadoanterior: EstadoDisponibilidadUnidad;
  estadonuevo: EstadoDisponibilidadUnidad;
  fechahora: number;
}

export interface HistorialEstadoUnidadItem extends HistorialEstadoUnidadData {
  idestadounidademergencia?: number;
  idusuario: number;
}

export interface UnidadEmergenciaResumen {
  idunidademergencia: number;
  nombre?: string;
  idtipounidad?: number;
  estado_actual: EstadoDisponibilidadUnidad;
  incluido_en_despacho: boolean;
}

export interface DeclararEstadoDisponibilidadRequest {
  estadonuevo: EstadoDisponibilidadUnidad;
}

export interface OfflineFotoRecord {
  local_id: string;
  idaccidente: string;
  blob: Blob;
  content_type: string;
  fechahora: number;
  object_url: string;
}

export interface OfflineNotaRecord {
  local_id: string;
  idaccidente: string;
  nota: string;
  tipo: TipoNotaCampo;
  fechahora: number;
}
