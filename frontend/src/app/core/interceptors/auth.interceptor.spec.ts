/** @marker unit */
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { AUTH_STORAGE_KEYS } from '../../modules/cuentas-clientes/auth/services/auth-api.types';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });

    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('adds Authorization header when access token exists', () => {
    // Arrange
    localStorage.setItem(AUTH_STORAGE_KEYS.accessToken, 'jwt-token-123');

    // Act
    http.get('/api/v1/protected').subscribe();

    // Assert
    const req = httpMock.expectOne('/api/v1/protected');
    expect(req.request.headers.get('Authorization')).toBe('Bearer jwt-token-123');
    req.flush({});
  });

  it('forwards request unchanged when no token is stored', () => {
    // Arrange
    // no token in localStorage

    // Act
    http.get('/api/v1/public').subscribe();

    // Assert
    const req = httpMock.expectOne('/api/v1/public');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });
});
