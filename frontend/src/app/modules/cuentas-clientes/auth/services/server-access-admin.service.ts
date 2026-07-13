import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  AssignServerRoleRequest,
  CreateServerRoleRequest,
  CreateServerUserRequest,
  ServerRole,
  ServerUser,
  UpdateServerRoleRequest,
  UpdateServerUserRequest,
} from './auth-api.types';

@Injectable({ providedIn: 'root' })
export class ServerAccessAdminService {
  private readonly http = inject(HttpClient);
  private readonly usersUrl = '/api/v1/usuarios-servidor';
  private readonly rolesUrl = '/api/v1/roles-servidor';

  listServerUsers(): Observable<ApiEnvelope<ServerUser[]>> {
    return this.http.get<ApiEnvelope<ServerUser[]>>(this.usersUrl);
  }

  getServerUser(idusuarioservidor: number): Observable<ApiEnvelope<ServerUser>> {
    return this.http.get<ApiEnvelope<ServerUser>>(`${this.usersUrl}/${idusuarioservidor}`);
  }

  createServerUser(request: CreateServerUserRequest): Observable<ApiEnvelope<ServerUser>> {
    return this.http.post<ApiEnvelope<ServerUser>>(this.usersUrl, request);
  }

  updateServerUser(
    idusuarioservidor: number,
    request: UpdateServerUserRequest,
  ): Observable<ApiEnvelope<ServerUser>> {
    return this.http.patch<ApiEnvelope<ServerUser>>(
      `${this.usersUrl}/${idusuarioservidor}`,
      request,
    );
  }

  deactivateServerUser(idusuarioservidor: number): Observable<ApiEnvelope<ServerUser>> {
    return this.updateServerUser(idusuarioservidor, { activo: false });
  }

  listServerRoles(): Observable<ApiEnvelope<ServerRole[]>> {
    return this.http.get<ApiEnvelope<ServerRole[]>>(this.rolesUrl);
  }

  createServerRole(request: CreateServerRoleRequest): Observable<ApiEnvelope<ServerRole>> {
    return this.http.post<ApiEnvelope<ServerRole>>(this.rolesUrl, request);
  }

  updateServerRole(
    idrolservidor: number,
    request: UpdateServerRoleRequest,
  ): Observable<ApiEnvelope<ServerRole>> {
    return this.http.patch<ApiEnvelope<ServerRole>>(`${this.rolesUrl}/${idrolservidor}`, request);
  }

  assignServerRole(request: AssignServerRoleRequest): Observable<ApiEnvelope<ServerUser>> {
    return this.http.post<ApiEnvelope<ServerUser>>(
      `${this.usersUrl}/${request.idusuarioservidor}/roles-servidor`,
      { idrolservidor: request.idrolservidor },
    );
  }
}
