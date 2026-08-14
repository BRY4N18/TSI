import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import type {
  CredencialEmitida,
  CredencialItem,
  EmitirCredencialRequest,
  Entorno,
  EstadoPartner,
  PartnerDetalle,
  PartnerListItem,
  EstadoAcceso,
  PartnerColaAcceso,
  ReactivacionAplicada,
  RegistrarPartnerRequest,
  RevocacionCredencial,
  SuspensionAplicada,
  ResolucionPromocionData,
  ResolucionPromocionRequest,
} from './models/partner.types';

export interface EnvelopeMeta {
  pagination: {
    next_cursor: number | null;
    /** Solo en `/logs-api`: su cursor es compuesto (fecha + id). */
    next_cursor_fecha?: number | null;
    limit: number;
  } | null;
}

export interface ApiEnvelope<T> {
  data: T;
  meta: EnvelopeMeta;
}

/** Cliente con suscripción vigente y sin partner previo. */
export interface ClienteElegible {
  idcliente: number;
  nombre: string;
}

export interface PartnerListFilters {
  estado?: EstadoPartner;
  limit?: number;
  cursor?: number | null;
}

/**
 * Cliente REST del módulo. Consume el contrato ya cerrado del backend; esta
 * capa no lo extiende salvo `GET /partners/me` (BE-DELTA-01), sin el cual el
 * portal del partner no puede cargar ninguna pantalla.
 */
@Injectable({ providedIn: 'root' })
export class PartnerApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/partners';

  // --- Consola -------------------------------------------------------------

  listar(filters: PartnerListFilters = {}): Observable<ApiEnvelope<PartnerListItem[]>> {
    let params = new HttpParams().set('limit', String(filters.limit ?? 20));
    if (filters.estado) {
      params = params.set('estado', filters.estado);
    }
    if (filters.cursor !== undefined && filters.cursor !== null) {
      params = params.set('cursor', String(filters.cursor));
    }
    return this.http.get<ApiEnvelope<PartnerListItem[]>>(this.base, { params });
  }

  /**
   * BE-DELTA-03 — clientes sobre los que se puede registrar un partner.
   *
   * El formulario de alta elige el cliente por nombre legible y no existía
   * ningún endpoint que expusiera clientes: sin esto el combobox queda vacío
   * y el registro es inalcanzable desde la UI (FR-UI-004).
   */
  clientesElegibles(): Observable<ApiEnvelope<ClienteElegible[]>> {
    return this.http.get<ApiEnvelope<ClienteElegible[]>>(`${this.base}/clientes-elegibles`);
  }

  detalle(idpartner: number): Observable<ApiEnvelope<PartnerDetalle>> {
    return this.http.get<ApiEnvelope<PartnerDetalle>>(`${this.base}/${idpartner}`);
  }

  registrar(
    body: RegistrarPartnerRequest,
    idempotencyKey: string,
  ): Observable<ApiEnvelope<PartnerListItem>> {
    return this.http.post<ApiEnvelope<PartnerListItem>>(this.base, body, {
      headers: this.conIdempotencia(idempotencyKey),
    });
  }

  asignarPlan(
    idpartner: number,
    idempotencyKey: string,
  ): Observable<ApiEnvelope<PartnerListItem>> {
    return this.http.post<ApiEnvelope<PartnerListItem>>(
      `${this.base}/${idpartner}/plan-acceso`,
      {},
      { headers: this.conIdempotencia(idempotencyKey) },
    );
  }

  resolverPromocion(
    idpartner: number,
    body: ResolucionPromocionRequest,
    idempotencyKey: string,
  ): Observable<ApiEnvelope<ResolucionPromocionData>> {
    return this.http.post<ApiEnvelope<ResolucionPromocionData>>(
      `${this.base}/${idpartner}/solicitud-produccion/resolucion`,
      body,
      { headers: this.conIdempotencia(idempotencyKey) },
    );
  }

  // --- Portal --------------------------------------------------------------

  /**
   * BE-DELTA-01 — primer requisito de todo el portal.
   *
   * El `Profile` de sesión solo trae `{idusuario, gmail, roles[]}` y todos los
   * demás endpoints exigen `{idpartner}` en la ruta: sin esta llamada el
   * partner no conoce su propio id y ninguna pantalla puede cargar.
   */
  miPartner(): Observable<ApiEnvelope<PartnerDetalle>> {
    return this.http.get<ApiEnvelope<PartnerDetalle>>(`${this.base}/me`);
  }

  listarCredenciales(
    idpartner: number,
    opciones: { entorno?: Entorno; soloActivas?: boolean } = {},
  ): Observable<ApiEnvelope<CredencialItem[]>> {
    let params = new HttpParams();
    if (opciones.entorno) {
      params = params.set('entorno', opciones.entorno);
    }
    if (opciones.soloActivas !== undefined) {
      params = params.set('solo_activas', String(opciones.soloActivas));
    }
    return this.http.get<ApiEnvelope<CredencialItem[]>>(
      `${this.base}/${idpartner}/credenciales`,
      { params },
    );
  }

  /**
   * La `Idempotency-Key` la genera quien llama, **por intento del usuario** y
   * no por reintento HTTP: es lo que hace que un reintento tras un timeout
   * devuelva el MISMO secreto en vez de emitir una credencial de más y perder
   * el secreto de la primera para siempre (FR-UI-023, RN-PON-005).
   */
  emitirCredencial(
    idpartner: number,
    body: EmitirCredencialRequest,
    idempotencyKey: string,
  ): Observable<ApiEnvelope<CredencialEmitida>> {
    return this.http.post<ApiEnvelope<CredencialEmitida>>(
      `${this.base}/${idpartner}/credenciales`,
      body,
      { headers: this.conIdempotencia(idempotencyKey) },
    );
  }

  /**
   * RF-PAC-001 / SRS §3.4.3: el partner revoca por sí mismo una credencial
   * comprometida y recibe **en el mismo acto** un reemplazo del mismo entorno y
   * nombre. Es autoservicio a propósito: "esperar autorización sería el peor
   * comportamiento posible" ante un incidente de seguridad.
   *
   * El endpoint existía desde el principio y **ninguna pantalla lo llamaba**.
   */
  revocarCredencial(
    idcredencial: number,
    motivo: string,
    idempotencyKey: string,
  ): Observable<ApiEnvelope<RevocacionCredencial>> {
    return this.http.post<ApiEnvelope<RevocacionCredencial>>(
      `/api/v1/credenciales/${idcredencial}/revocar`,
      { motivo },
      { headers: this.conIdempotencia(idempotencyKey) },
    );
  }

  solicitarProduccion(
    idpartner: number,
    nombreCredencial: string,
    idempotencyKey: string,
  ): Observable<ApiEnvelope<{ idpartner: number; estado: EstadoPartner }>> {
    return this.http.post<ApiEnvelope<{ idpartner: number; estado: EstadoPartner }>>(
      `${this.base}/${idpartner}/solicitud-produccion`,
      { nombre_credencial: nombreCredencial },
      { headers: this.conIdempotencia(idempotencyKey) },
    );
  }

  // --- Gestión de acceso (RF-PAC-005 / RF-PAC-009) -------------------------

  /** Cola del Administrador: suspendidos y en ciclo de mora (RF-PAC-009 b). */
  colaAcceso(): Observable<ApiEnvelope<PartnerColaAcceso[]>> {
    return this.http.get<ApiEnvelope<PartnerColaAcceso[]>>(`${this.base}/cola-acceso`);
  }

  /**
   * Estado de acceso de un partner (RF-PAC-009 a). Un partner **suspendido** sí
   * puede consultarlo: es lectura y es justo donde entiende por qué se le cortó
   * el acceso y qué debe hacer (RN-PAC-016).
   */
  estadoAcceso(idpartner: number): Observable<ApiEnvelope<EstadoAcceso>> {
    return this.http.get<ApiEnvelope<EstadoAcceso>>(`${this.base}/${idpartner}/estado-acceso`);
  }

  suspender(
    idpartner: number,
    motivo: string,
    idempotencyKey: string,
  ): Observable<ApiEnvelope<SuspensionAplicada>> {
    return this.http.post<ApiEnvelope<SuspensionAplicada>>(
      `${this.base}/${idpartner}/suspender`,
      { motivo },
      { headers: this.conIdempotencia(idempotencyKey) },
    );
  }

  /** El sistema nunca reactiva solo (RN-PAC-009): siempre lo confirma un Administrador. */
  reactivar(
    idpartner: number,
    motivo: string,
    idempotencyKey: string,
  ): Observable<ApiEnvelope<ReactivacionAplicada>> {
    return this.http.post<ApiEnvelope<ReactivacionAplicada>>(
      `${this.base}/${idpartner}/reactivar`,
      { motivo },
      { headers: this.conIdempotencia(idempotencyKey) },
    );
  }

  private conIdempotencia(key: string): HttpHeaders {
    return new HttpHeaders({ 'Idempotency-Key': key });
  }
}

/** UUID v4 por intento del usuario. Se reutiliza al reintentar. */
export function nuevaClaveIdempotencia(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `k-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}
