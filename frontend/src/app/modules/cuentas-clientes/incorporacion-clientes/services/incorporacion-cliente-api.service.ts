import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  CompletarEtapaData,
  CompletarEtapaRequest,
  ConfiguracionCuentaData,
  ConfiguracionCuentaRequest,
  LogoUploadUrlData,
  OnboardingProgresoData,
  RegistroCuentaData,
  RegistroCuentaRequest,
  ReenviarInvitacionData,
  ReenviarInvitacionRequest,
} from '../models/incorporacion-cliente.contract';

@Injectable({ providedIn: 'root' })
export class IncorporacionClienteApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/cuentas-clientes';

  registrarCuenta(body: RegistroCuentaRequest): Observable<ApiEnvelope<RegistroCuentaData>> {
    return this.http.post<ApiEnvelope<RegistroCuentaData>>(this.base, body);
  }

  configurarCuenta(
    idcliente: number,
    body: ConfiguracionCuentaRequest,
  ): Observable<ApiEnvelope<ConfiguracionCuentaData>> {
    return this.http.patch<ApiEnvelope<ConfiguracionCuentaData>>(
      `${this.base}/${idcliente}/configuracion`,
      body,
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
