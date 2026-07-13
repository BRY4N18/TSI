import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  BajaCuentaData,
  LogoUploadUrlData,
  PerfilData,
  PerfilUpdatedData,
  PreferenciasData,
  PreferenciasUpdatedData,
  TransferenciaPropiedadData,
  UsuarioElegible,
} from '../models/cuenta-cliente.contract';

@Injectable({ providedIn: 'root' })
export class CuentaClienteApiService {
  private readonly http = inject(HttpClient);

  private baseUrl(idcliente: number): string {
    return `/api/v1/cuentas-clientes/${idcliente}`;
  }

  getPerfil(idcliente: number): Observable<ApiEnvelope<PerfilData>> {
    return this.http.get<ApiEnvelope<PerfilData>>(`${this.baseUrl(idcliente)}/perfil`);
  }

  patchPerfil(
    idcliente: number,
    body: Partial<Pick<PerfilData, 'razon_social' | 'nombre' | 'logo_url'>>,
  ): Observable<ApiEnvelope<PerfilUpdatedData>> {
    return this.http.patch<ApiEnvelope<PerfilUpdatedData>>(
      `${this.baseUrl(idcliente)}/perfil`,
      body,
    );
  }

  getPreferencias(idcliente: number): Observable<ApiEnvelope<PreferenciasData>> {
    return this.http.get<ApiEnvelope<PreferenciasData>>(
      `${this.baseUrl(idcliente)}/preferencias`,
    );
  }

  patchPreferencias(
    idcliente: number,
    body: Partial<Omit<PreferenciasData, 'id_preferencia' | 'id_cliente'>>,
  ): Observable<ApiEnvelope<PreferenciasUpdatedData>> {
    return this.http.patch<ApiEnvelope<PreferenciasUpdatedData>>(
      `${this.baseUrl(idcliente)}/preferencias`,
      body,
    );
  }

  createLogoUploadUrl(
    idcliente: number,
    contentType: string,
    fileName?: string,
  ): Observable<ApiEnvelope<LogoUploadUrlData>> {
    return this.http.post<ApiEnvelope<LogoUploadUrlData>>(
      `${this.baseUrl(idcliente)}/logo/upload-url`,
      { content_type: contentType, file_name: fileName },
    );
  }

  listUsuariosElegibles(
    idcliente: number,
  ): Observable<ApiEnvelope<{ usuarios: UsuarioElegible[] }>> {
    return this.http.get<ApiEnvelope<{ usuarios: UsuarioElegible[] }>>(
      `${this.baseUrl(idcliente)}/usuarios-elegibles`,
    );
  }

  transferirPropiedad(
    idcliente: number,
    idNuevoResponsable: number,
  ): Observable<ApiEnvelope<TransferenciaPropiedadData>> {
    return this.http.post<ApiEnvelope<TransferenciaPropiedadData>>(
      `${this.baseUrl(idcliente)}/transferencia-propiedad`,
      { id_nuevo_responsable: idNuevoResponsable },
    );
  }

  darBaja(
    idcliente: number,
    motivo?: string,
  ): Observable<ApiEnvelope<BajaCuentaData>> {
    return this.http.post<ApiEnvelope<BajaCuentaData>>(
      `${this.baseUrl(idcliente)}/baja`,
      motivo ? { motivo } : {},
    );
  }
}
