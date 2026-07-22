export type EstadoRegion = 'En_Validación' | 'Producción' | 'En_Alerta' | 'Despublicada';

export type ResultadoValidacion = 'Aprobada' | 'Rechazada';

export interface RegionOperativaData {
  idregionoperativa: number;
  idestado: number;
  nombreregion: string;
  estadoregion: EstadoRegion;
  activo: boolean;
}

export interface ApiEnvelope<T> {
  data: T;
  meta?: { pagination: object | null };
}

export interface ValidacionRegionRequest {
  idregionoperativa?: number;
  idestado?: number;
  nombreregion?: string;
  resultado: ResultadoValidacion;
  motivo?: string;
}

export interface ValidacionRegionData {
  idregionoperativa: number;
  idvalidacionregion: number;
  resultado: ResultadoValidacion;
  estadoregion_actual: EstadoRegion;
}

export interface ValidacionHistorialItem {
  idvalidacionregion: number;
  idregionoperativa: number;
  idusuario: number;
  resultado: ResultadoValidacion;
  motivo: string | null;
  fechahora: number;
}

export interface RechazoDefinitivoData {
  idregionoperativa: number;
  activo: boolean;
}

export interface ReevaluacionRequest {
  estadoregion: 'En_Alerta' | 'Despublicada';
  motivo: string;
}

export interface RegionEstadoData {
  idregionoperativa: number;
  estadoregion: EstadoRegion;
}
