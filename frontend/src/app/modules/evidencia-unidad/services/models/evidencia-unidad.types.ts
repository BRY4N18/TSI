export type EstadoDisponibilidadUnidad = 'Activa' | 'Ocupada' | 'En Misión' | 'Fuera de servicio';

/** "En Misión" es de asignación exclusiva del sistema (despacho-inteligente); no es declarable manualmente. */
export type EstadoDisponibilidadUnidadSeleccionable = 'Activa' | 'Ocupada' | 'Fuera de servicio';

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
  placa: string | null;
  tipounidademergencia: string | null;
  capacidad: string | null;
  idcondado: number | null;
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
  /** Tipo de unidad: "Ambulancia", "Grúa", … (texto, no id). */
  tipounidademergencia?: string;
  placa?: string;
  estado_actual: EstadoDisponibilidadUnidad;
  incluido_en_despacho: boolean;
}

export interface DeclararEstadoDisponibilidadRequest {
  estadonuevo: EstadoDisponibilidadUnidadSeleccionable;
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

export interface UpsertClimaAccidenteRequest {
  idperiododia?: number | null;
  idestadoclima?: number | null;
}

export interface ClimaAccidenteData {
  idelementoclimaticoaccidente?: number;
  idaccidente: string;
  idperiododia: number | null;
  idestadoclima: number | null;
  activo: boolean;
  fecha_actualizacion?: number;
}

export interface ElementoFisicoAccidenteItem {
  idelementosfisicosaccidente: number;
  idaccidente: string;
  idelementofisico: number;
  elementofisico?: string;
  activo: boolean;
  fecha_actualizacion?: number;
}

export interface ConductorPayload {
  identificacion: string;
  nombres: string;
  apellidos: string;
  genero?: string | null;
  tipolicencia?: string | null;
  estadolicencia?: string | null;
  ciudadresidencia?: string | null;
  aniosexperiencia?: number | null;
}

export interface VehiculoPayload {
  idvehiculo?: number;
  tipovehiculo: string;
  modelovehiculo?: string | null;
  categoriausovehiculo?: string | null;
  mercanciapeligrosa?: boolean | null;
  ejes?: number | null;
}

export interface RegistrarConductorAccidenteRequest {
  conductor: ConductorPayload;
  idestadoconductor: number;
  vehiculo: VehiculoPayload;
}

export interface ConductorAccidenteItem {
  idconductoraccidente: number;
  idaccidente: string;
  idconductor: number;
  idestadoconductor: number;
  idvehiculo: number;
  activo: boolean;
  fecha_actualizacion?: number;
  conductor: ConductorPayload;
  vehiculo: VehiculoPayload;
}

export interface EnriquecimientoAccidenteData {
  idaccidente: string;
  clima: ClimaAccidenteData | null;
  elementos_fisicos: ElementoFisicoAccidenteItem[];
  conductores: ConductorAccidenteItem[];
  implicados: ImplicadoItem[];
}

export type TipoImplicado = 'Peaton' | 'Pasajero' | 'Testigo' | 'Otro';
export type EstadoImplicado = 'Ileso' | 'Lesionado' | 'Fallecido' | 'Desconocido';

export interface RegistrarImplicadoRequest {
  tipoimplicado: TipoImplicado;
  estadoimplicado: EstadoImplicado;
  genero?: string | null;
  edad?: number | null;
}

export interface ImplicadoItem {
  idimplicado: number;
  idaccidente: string;
  tipoimplicado: string;
  estadoimplicado: string;
  genero?: string | null;
  edad?: number | null;
  activo: boolean;
  fecha_actualizacion?: number;
}

export interface CatalogoItem {
  [key: string]: string | number | boolean | null | undefined;
}

export interface CatalogoListData {
  items: CatalogoItem[];
}

export interface OfflineClimaRecord {
  local_id: string;
  idaccidente: string;
  idperiododia: number | null;
  idestadoclima: number | null;
  fechahora: number;
}

export interface OfflineFisicoRecord {
  local_id: string;
  idaccidente: string;
  idelementofisico: number;
  fechahora: number;
}

/** PII cifrada at-rest (AES-GCM); nunca persistir identificacion/nombres/apellidos en claro. */
export interface OfflineConductorRecord {
  local_id: string;
  idaccidente: string;
  idestadoconductor: number;
  tipovehiculo: string;
  modelovehiculo?: string | null;
  ciphertext: string;
  iv: string;
  fechahora: number;
}

/** Offline sin PII — ontología Dim_Implicado (Decision 13). */
export interface OfflineImplicadoRecord {
  local_id: string;
  idaccidente: string;
  tipoimplicado: TipoImplicado;
  estadoimplicado: EstadoImplicado;
  genero?: string | null;
  edad?: number | null;
  fechahora: number;
}

export interface DecryptedConductorPendiente {
  local_id: string;
  idaccidente: string;
  idestadoconductor: number;
  conductor: ConductorPayload;
  vehiculo: VehiculoPayload;
  fechahora: number;
}

export interface DecryptedImplicadoPendiente {
  local_id: string;
  idaccidente: string;
  payload: RegistrarImplicadoRequest;
  fechahora: number;
}

export interface SincronizarEnriquecimientoPayload {
  clima?: OfflineClimaRecord;
  elementos_fisicos?: OfflineFisicoRecord[];
  conductores?: Array<{
    local_id: string;
    conductor: ConductorPayload;
    idestadoconductor: number;
    vehiculo: VehiculoPayload;
  }>;
  implicados?: Array<{ local_id: string } & RegistrarImplicadoRequest>;
}
