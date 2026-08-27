import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ApiEnvelope,
  AssignBusinessRoleRequest,
  BusinessRole,
  BusinessUser,
  CreateBusinessRoleRequest,
  CreateBusinessUserRequest,
  UpdateBusinessRoleRequest,
  UpdateBusinessUserRequest,
} from './auth-api.types';

@Injectable({ providedIn: 'root' })
export class UserRoleAdminService {
  private readonly http = inject(HttpClient);
  private readonly usersUrl = '/api/v1/usuarios';
  private readonly rolesUrl = '/api/v1/roles';

  listUsers(): Observable<ApiEnvelope<BusinessUser[]>> {
    return this.http.get<ApiEnvelope<BusinessUser[]>>(this.usersUrl);
  }

  getUser(idusuario: number): Observable<ApiEnvelope<BusinessUser>> {
    return this.http.get<ApiEnvelope<BusinessUser>>(`${this.usersUrl}/${idusuario}`);
  }

  createUser(request: CreateBusinessUserRequest): Observable<ApiEnvelope<BusinessUser>> {
    return this.http.post<ApiEnvelope<BusinessUser>>(this.usersUrl, request);
  }

  updateUser(
    idusuario: number,
    request: UpdateBusinessUserRequest,
  ): Observable<ApiEnvelope<BusinessUser>> {
    return this.http.patch<ApiEnvelope<BusinessUser>>(`${this.usersUrl}/${idusuario}`, request);
  }

  deactivateUser(idusuario: number): Observable<ApiEnvelope<BusinessUser>> {
    return this.updateUser(idusuario, { activo: false });
  }

  listRoles(): Observable<ApiEnvelope<BusinessRole[]>> {
    return this.http.get<ApiEnvelope<BusinessRole[]>>(this.rolesUrl);
  }

  createRole(request: CreateBusinessRoleRequest): Observable<ApiEnvelope<BusinessRole>> {
    return this.http.post<ApiEnvelope<BusinessRole>>(this.rolesUrl, request);
  }

  updateRole(
    idrol: number,
    request: UpdateBusinessRoleRequest,
  ): Observable<ApiEnvelope<BusinessRole>> {
    return this.http.patch<ApiEnvelope<BusinessRole>>(`${this.rolesUrl}/${idrol}`, request);
  }

  assignRole(request: AssignBusinessRoleRequest): Observable<ApiEnvelope<BusinessUser>> {
    // Backend registra `usuarios/roles/asignar` (ver `apps/cuentas_clientes/views/urls.py`),
    // no `usuarios/{id}/roles` — ese otro shape daba 404 y el formulario de
    // "Asignar rol" en Gestión de cuenta fallaba siempre con "No se pudo asignar el rol".
    return this.http.post<ApiEnvelope<BusinessUser>>(
      `${this.usersUrl}/roles/asignar`,
      { idusuario: request.idusuario, idrol: request.idrol },
    );
  }
}
