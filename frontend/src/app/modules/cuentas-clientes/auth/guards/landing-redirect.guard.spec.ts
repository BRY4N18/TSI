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
      'getCuenta',
    ]);
    authApi.requiresPasswordChange.and.returnValue(false);
    // Sin cuenta de cliente asociada: el guard resuelve por rol.
    authApi.getCuenta.and.returnValue(null);

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
  it('con_incorporacion_pendiente_va_al_asistente', () => {
    // Arrange — la cuenta aún no está lista para operar (SRS §3.2.2).
    authApi.isAuthenticated.and.returnValue(true);
    authApi.getProfile.and.returnValue({ idusuario: 9002, gmail: 'x@y.z', roles: ['Cliente'] });
    authApi.getCuenta.and.returnValue({
      idcliente: 920003,
      estadoOnboarding: 'Pendiente',
      onboardingPendiente: true,
    });

    // Act
    const destino = ejecutar();

    // Assert
    expect(TestBed.inject(Router).serializeUrl(destino)).toBe(
      '/cuentas-clientes/incorporacion-clientes/920003/onboarding',
    );
  });
});
