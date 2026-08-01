/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router, UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../services/auth-api.service';
import { landingRedirectGuard } from './landing-redirect.guard';

describe('landingRedirectGuard', () => {
  let authApi: jasmine.SpyObj<AuthApiService>;

  function ejecutar(): UrlTree {
    return TestBed.runInInjectionContext(
      () => landingRedirectGuard({} as any, {} as any) as UrlTree,
    );
  }

  beforeEach(() => {
    authApi = jasmine.createSpyObj('AuthApiService', [
      'isAuthenticated',
      'requiresPasswordChange',
      'getProfile',
    ]);
    authApi.requiresPasswordChange.and.returnValue(false);

    TestBed.configureTestingModule({
      providers: [{ provide: AuthApiService, useValue: authApi }, provideRouter([])],
    });
  });

  it('sin_sesion_va_al_portal_comercial_publico', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(false);

    // Act
    const destino = ejecutar();

    // Assert
    expect(TestBed.inject(Router).serializeUrl(destino)).toBe('/ventas-crm/planes');
  });

  it('con_sesion_va_al_home_del_rol_no_al_portal_publico', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.getProfile.and.returnValue({ idusuario: 1, gmail: 'op@tsi.com', roles: ['Operador'] } as any);

    // Act
    const destino = ejecutar();

    // Assert
    expect(TestBed.inject(Router).serializeUrl(destino)).toBe('/accidentes/lista');
  });

  it('con_sesion_de_administrador_va_a_su_home', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.getProfile.and.returnValue({
      idusuario: 2,
      gmail: 'admin@tsi.com',
      roles: ['Administrador'],
    } as any);

    // Act
    const destino = ejecutar();

    // Assert
    expect(TestBed.inject(Router).serializeUrl(destino)).toBe('/cuentas-clientes');
  });

  it('si_debe_cambiar_password_va_al_reset_forzado', () => {
    // Arrange
    authApi.isAuthenticated.and.returnValue(true);
    authApi.requiresPasswordChange.and.returnValue(true);

    // Act
    const destino = ejecutar();

    // Assert
    expect(TestBed.inject(Router).serializeUrl(destino)).toBe(
      '/cuentas-clientes/auth/password-reset?forced=true',
    );
  });
});
