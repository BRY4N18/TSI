import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, tap } from 'rxjs';

import {
  AUTH_STORAGE_KEYS,
  LoginRequest,
  LoginSuccessResponse,
  Profile,
  RevokeSessionRequest,
  SessionClosedResponse,
  SessionRevokedResponse,
} from './auth-api.types';

@Injectable({ providedIn: 'root' })
export class AuthApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/auth';

  login(request: LoginRequest): Observable<LoginSuccessResponse> {
    return this.http
      .post<LoginSuccessResponse>(`${this.baseUrl}/login`, request)
      .pipe(tap((response) => this.persistSession(response)));
  }

  logout(): Observable<SessionClosedResponse> {
    return this.http
      .post<SessionClosedResponse>(`${this.baseUrl}/logout`, {})
      .pipe(tap(() => this.clearSession()));
  }

  revokeSession(request: RevokeSessionRequest): Observable<SessionRevokedResponse> {
    return this.http.post<SessionRevokedResponse>(`${this.baseUrl}/revoke-session`, request);
  }

  getAccessToken(): string | null {
    return localStorage.getItem(AUTH_STORAGE_KEYS.accessToken);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(AUTH_STORAGE_KEYS.refreshToken);
  }

  getProfile(): Profile | null {
    const raw = localStorage.getItem(AUTH_STORAGE_KEYS.profile);
    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw) as Profile;
    } catch {
      return null;
    }
  }

  requiresPasswordChange(): boolean {
    return localStorage.getItem(AUTH_STORAGE_KEYS.requiresPasswordChange) === 'true';
  }

  isAuthenticated(): boolean {
    return Boolean(this.getAccessToken() && this.getProfile());
  }

  hasRole(role: string): boolean {
    const profile = this.getProfile();
    return profile?.roles.includes(role) ?? false;
  }

  hasAnyRole(roles: string[]): boolean {
    return roles.some((role) => this.hasRole(role));
  }

  clearSession(): void {
    localStorage.removeItem(AUTH_STORAGE_KEYS.accessToken);
    localStorage.removeItem(AUTH_STORAGE_KEYS.refreshToken);
    localStorage.removeItem(AUTH_STORAGE_KEYS.profile);
    localStorage.removeItem(AUTH_STORAGE_KEYS.requiresPasswordChange);
  }

  private persistSession(response: LoginSuccessResponse): void {
    const { accessToken, refreshToken, profile, requiresPasswordChange } = response.data;

    localStorage.setItem(AUTH_STORAGE_KEYS.accessToken, accessToken);
    localStorage.setItem(AUTH_STORAGE_KEYS.refreshToken, refreshToken);
    localStorage.setItem(AUTH_STORAGE_KEYS.profile, JSON.stringify(profile));
    localStorage.setItem(
      AUTH_STORAGE_KEYS.requiresPasswordChange,
      String(requiresPasswordChange),
    );
  }
}
