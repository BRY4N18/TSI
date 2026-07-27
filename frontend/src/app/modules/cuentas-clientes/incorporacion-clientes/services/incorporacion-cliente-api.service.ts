import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  AprobacionData,
  AprobacionRequest,
  AutorregistroProveedorData,
  AutorregistroProveedorRequest,
  CompletarEtapaData,
  CompletarEtapaRequest,
  LogoUploadUrlData,
  OnboardingProgresoData,
  ReenviarInvitacionData,
  ReenviarInvitacionRequest,
  SolicitudItem,
} from '../models/incorporacion-cliente.contract';

@Injectable({ providedIn: 'root' })
export class IncorporacionClienteApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/cuentas-clientes';

  autorregistrar(
    body: AutorregistroProveedorRequest,
  ): Observable<ApiEnvelope<AutorregistroProveedorData>> {
    return this.http.post<ApiEnvelope<AutorregistroProveedorData>>(
      `${this.base}/autorregistro`,
      body,
    );
  }

  listarSolicitudes(
    estado: 'Pendiente_Aprobación' | 'Rechazado' = 'Pendiente_Aprobación',
  ): Observable<ApiEnvelope<SolicitudItem[]>> {
    return this.http.get<ApiEnvelope<SolicitudItem[]>>(`${this.base}/solicitudes`, {
      params: { estado },
    });
  }

  decidirSolicitud(
    idcliente: number,
    body: AprobacionRequest,
  ): Observable<ApiEnvelope<AprobacionData>> {
    return this.http.post<ApiEnvelope<AprobacionData>>(
      `${this.base}/${idcliente}/aprobacion`,
      body,
    );
  }

  anularRechazo(idcliente: number): Observable<ApiEnvelope<AprobacionData>> {
    return this.http.post<ApiEnvelope<AprobacionData>>(
      `${this.base}/${idcliente}/anular-rechazo`,
      {},
    );
  }

  createLogoUploadUrl(
    idcliente: number,
    contentType: string,
    fileName?: string,
  ): Observable<ApiEnvelope<LogoUploadUrlData>> {
    return this.http.post<ApiEnvelope<LogoUploadUrlData>>(
      `${this.base}/${idcliente}/logo/upload-url`,
      { content_type: contentType, file_name: fileName },
    );
  }

  getOnboardingProgreso(idcliente: number): Observable<ApiEnvelope<OnboardingProgresoData>> {
    return this.http.get<ApiEnvelope<OnboardingProgresoData>>(
      `${this.base}/${idcliente}/onboarding/progreso`,
    );
  }

  completarEtapa(
    idcliente: number,
    body: CompletarEtapaRequest,
  ): Observable<ApiEnvelope<CompletarEtapaData>> {
    return this.http.post<ApiEnvelope<CompletarEtapaData>>(
      `${this.base}/${idcliente}/onboarding/etapas`,
      body,
    );
  }

  reenviarInvitacion(
    idcliente: number,
    body?: ReenviarInvitacionRequest,
  ): Observable<ApiEnvelope<ReenviarInvitacionData>> {
    return this.http.post<ApiEnvelope<ReenviarInvitacionData>>(
      `${this.base}/${idcliente}/invitacion/reenviar`,
      body ?? {},
    );
  }
}
