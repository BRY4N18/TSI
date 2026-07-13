/** @marker unit */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';

import { AuthApiService } from '../services/auth-api.service';
import { LoginPage } from './login.page';

describe('LoginPage', () => {
  let fixture: ComponentFixture<LoginPage>;
  let authApi: jasmine.SpyObj<AuthApiService>;
  let router: Router;

  beforeEach(async () => {
    authApi = jasmine.createSpyObj('AuthApiService', ['login', 'logout', 'clearSession']);

    await TestBed.configureTestingModule({
      imports: [LoginPage, RouterTestingModule],
      providers: [
        { provide: AuthApiService, useValue: authApi },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { queryParamMap: convertToParamMap({}) } },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginPage);
    router = TestBed.inject(Router);
    spyOn(router, 'navigateByUrl').and.resolveTo(true);
    spyOn(router, 'navigate').and.resolveTo(true);
    fixture.detectChanges();
  });

  function fillForm(gmail: string, password: string): void {
    fixture.componentInstance.form.setValue({ gmail, password });
  }

  it('onSubmit_when_success_navigates_to_returnUrl', () => {
    // Arrange
    authApi.login.and.returnValue(
      of<any>({
        data: {
          accessToken: 'a',
          refreshToken: 'r',
          tokenType: 'Bearer',
          expiresInSeconds: 3600,
          profile: { idusuario: 1, gmail: 'user@test.com', roles: [] },
          requiresPasswordChange: false,
        },
        meta: {},
      }),
    );
    fillForm('user@test.com', 'password123');

    // Act
    fixture.componentInstance.onSubmit();

    // Assert
    expect(authApi.login).toHaveBeenCalledWith({
      gmail: 'user@test.com',
      password: 'password123',
    });
    expect(router.navigateByUrl).toHaveBeenCalledWith('/cuentas-clientes');
    expect(fixture.componentInstance.loading()).toBeFalse();
  });

  it('onSubmit_when_requires_password_change_navigates_to_password_reset', () => {
    // Arrange
    authApi.login.and.returnValue(
      of<any>({
        data: {
          accessToken: 'a',
          refreshToken: 'r',
          tokenType: 'Bearer',
          expiresInSeconds: 3600,
          profile: { idusuario: 1, gmail: 'user@test.com', roles: [] },
          requiresPasswordChange: true,
        },
        meta: {},
      }),
    );
    fillForm('user@test.com', 'password123');

    // Act
    fixture.componentInstance.onSubmit();

    // Assert
    expect(router.navigate).toHaveBeenCalledWith(['/cuentas-clientes/auth/password-reset'], {
      queryParams: { forced: 'true' },
    });
  });

  it('onSubmit_when_invalid_credentials_shows_error_message', () => {
    // Arrange
    authApi.login.and.returnValue(throwError(() => ({ status: 401 })));
    fillForm('user@test.com', 'password123');

    // Act
    fixture.componentInstance.onSubmit();

    // Assert
    expect(fixture.componentInstance.errorMessage()).toBe(
      'Credenciales inválidas o usuario inactivo.',
    );
    expect(fixture.componentInstance.loading()).toBeFalse();
  });

  it('onSubmit_when_account_locked_error_shows_generic_error_message', () => {
    // Arrange: backend represents blocked accounts as an inactive-user 401/403
    authApi.login.and.returnValue(throwError(() => ({ status: 403 })));
    fillForm('user@test.com', 'password123');

    // Act
    fixture.componentInstance.onSubmit();

    // Assert
    expect(fixture.componentInstance.errorMessage()).toBe(
      'Credenciales inválidas o usuario inactivo.',
    );
  });

  it('onSubmit_when_form_invalid_does_not_call_login', () => {
    // Arrange
    fillForm('not-an-email', '');

    // Act
    fixture.componentInstance.onSubmit();

    // Assert
    expect(authApi.login).not.toHaveBeenCalled();
  });
});
