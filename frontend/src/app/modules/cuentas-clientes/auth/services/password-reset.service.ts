import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { PasswordResetRequest, PasswordResetResponse } from './auth-api.types';

@Injectable({ providedIn: 'root' })
export class PasswordResetService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/auth/password-reset';

  requestReset(request: PasswordResetRequest): Observable<PasswordResetResponse> {
    return this.http.post<PasswordResetResponse>(this.baseUrl, request);
  }

  /**
   * Define la contraseña definitiva del usuario autenticado (CU-O04). Es el paso
   * que desbloquea a quien entró con una credencial temporal.
   */
  changePassword(request: {
    password_actual: string;
    password_nueva: string;
  }): Observable<{ data: { message: string } }> {
    return this.http.post<{ data: { message: string } }>(
      '/api/v1/auth/password-change',
      request,
    );
  }
}
