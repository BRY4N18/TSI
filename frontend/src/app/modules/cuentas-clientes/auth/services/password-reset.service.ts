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
}
