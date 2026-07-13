/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { AUTH_STORAGE_KEYS } from './auth-api.types';
import { AuthApiService } from './auth-api.service';

describe('AuthApiService', () => {
  let service: AuthApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();

    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(AuthApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('login_when_success_persists_tokens_and_profile', () => {
    // Arrange
    const response = {
      data: {
        accessToken: 'access-1',
        refreshToken: 'refresh-1',
        tokenType: 'Bearer',
        expiresInSeconds: 3600,
        profile: { idusuario: 1, gmail: 'user@test.com', roles: ['Operador'] },
        requiresPasswordChange: false,
      },
      meta: {},
    };

    // Act
    service.login({ gmail: 'user@test.com', password: 'secret' }).subscribe((res) => {
      expect(res.data.accessToken).toBe('access-1');
    });

    const req = httpMock.expectOne('/api/v1/auth/login');
    expect(req.request.method).toBe('POST');
    req.flush(response);

    // Assert
    expect(localStorage.getItem(AUTH_STORAGE_KEYS.accessToken)).toBe('access-1');
    expect(localStorage.getItem(AUTH_STORAGE_KEYS.refreshToken)).toBe('refresh-1');
    expect(localStorage.getItem(AUTH_STORAGE_KEYS.requiresPasswordChange)).toBe('false');
    expect(service.isAuthenticated()).toBeTrue();
  });

  it('logout_when_called_clears_session', () => {
    // Arrange
    localStorage.setItem(AUTH_STORAGE_KEYS.accessToken, 'access-1');
    localStorage.setItem(AUTH_STORAGE_KEYS.refreshToken, 'refresh-1');
    localStorage.setItem(
      AUTH_STORAGE_KEYS.profile,
      JSON.stringify({ idusuario: 1, gmail: 'user@test.com', roles: [] }),
    );

    // Act
    service.logout().subscribe();
    const req = httpMock.expectOne('/api/v1/auth/logout');
    expect(req.request.method).toBe('POST');
    req.flush({
      data: { sessionId: 1, status: 'Cierre sesion', closedAt: '2026-07-11T00:00:00Z' },
      meta: {},
    });

    // Assert
    expect(localStorage.getItem(AUTH_STORAGE_KEYS.accessToken)).toBeNull();
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('revokeSession_when_called_does_not_persist_local_session', () => {
    // Arrange
    localStorage.setItem(AUTH_STORAGE_KEYS.accessToken, 'access-1');
    localStorage.setItem(
      AUTH_STORAGE_KEYS.profile,
      JSON.stringify({ idusuario: 1, gmail: 'user@test.com', roles: [] }),
    );

    // Act
    service.revokeSession({ idsession: 5 }).subscribe((res) => {
      expect(res.data.status).toBe('Expulsado');
    });
    const req = httpMock.expectOne('/api/v1/auth/revoke-session');
    expect(req.request.method).toBe('POST');
    req.flush({
      data: { sessionId: 5, status: 'Expulsado', revokedAt: '2026-07-11T00:00:00Z' },
      meta: {},
    });

    // Assert: local session for the caller is unaffected
    expect(localStorage.getItem(AUTH_STORAGE_KEYS.accessToken)).toBe('access-1');
    expect(service.isAuthenticated()).toBeTrue();
  });
});
