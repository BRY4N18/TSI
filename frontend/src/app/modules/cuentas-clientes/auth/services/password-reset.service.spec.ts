/** @marker unit */
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { PasswordResetService } from './password-reset.service';

describe('PasswordResetService', () => {
  let service: PasswordResetService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(PasswordResetService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('posts password reset request to contract endpoint', () => {
    // Arrange
    const request = { gmail: 'user@example.com' };
    const response = {
      data: {
        message: 'Password reset email sent',
        credentialStatus: 'Cambio contraseña' as const,
      },
      meta: { pagination: null },
    };

    // Act
    service.requestReset(request).subscribe((value) => {
      expect(value.data.message).toBe('Password reset email sent');
    });

    // Assert
    const req = httpMock.expectOne('/api/v1/auth/password-reset');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(request);
    req.flush(response);
  });
});
