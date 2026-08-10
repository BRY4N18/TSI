/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';
import { ROL_RESUELVE_PROMOCION, administradorPromocionGuard } from './administrador-promocion.guard';
import { ROLES_GESTOR_PARTNERS, gestorPartnersGuard } from './gestor-partners.guard';
import { ROL_PARTNER_INTEGRACION, partnerIntegracionGuard } from './partner-integracion.guard';

describe('guards de Partners y API', () => {
  let authApi: jasmine.SpyObj<AuthApiService>;
  let router: Router;

  const LOGIN = ['/cuentas-clientes/auth/login'];
  const DENEGADO = ['/cuentas-clientes/auth/access-denied'];

  beforeEach(() => {
    authApi = jasmine.createSpyObj<AuthApiService>('AuthApiService', [
      'isAuthenticated',
      'hasAnyRole',
      'hasRole',
    ]);

    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      providers: [{ provide: AuthApiService, useValue: authApi }],
    });

    router = TestBed.inject(Router);
  });

  const ejecutar = (guard: typeof gestorPartnersGuard) =>
    TestBed.runInInjectionContext(() => guard({} as never, {} as never));

  describe('gestorPartnersGuard', () => {
    it('redirige a login si no hay sesión', () => {
      // Arrange
      authApi.isAuthenticated.and.returnValue(false);

      // Act
      const resultado = ejecutar(gestorPartnersGuard);

      // Assert
      expect(resultado).toEqual(router.createUrlTree(LOGIN));
    });

    it('deniega a quien no gestiona partners', () => {
      // Arrange
      authApi.isAuthenticated.and.returnValue(true);
      authApi.hasAnyRole.and.returnValue(false);

      // Act
      const resultado = ejecutar(gestorPartnersGuard);

      // Assert
      expect(resultado).toEqual(router.createUrlTree(DENEGADO));
      expect(authApi.hasAnyRole).toHaveBeenCalledWith(ROLES_GESTOR_PARTNERS);
    });

    it('permite a Administrador y a Desarrollador de APIs', () => {
      // Arrange
      authApi.isAuthenticated.and.returnValue(true);
      authApi.hasAnyRole.and.returnValue(true);

      // Act / Assert
      expect(ejecutar(gestorPartnersGuard)).toBeTrue();
      expect(ROLES_GESTOR_PARTNERS).toEqual(['Administrador', 'DesarrolladorAPIs']);
    });
  });

  describe('administradorPromocionGuard — RF-PON-008', () => {
    it('permite al Administrador', () => {
      // Arrange
      authApi.isAuthenticated.and.returnValue(true);
      authApi.hasRole.and.returnValue(true);

      // Act / Assert
      expect(ejecutar(administradorPromocionGuard)).toBeTrue();
      expect(authApi.hasRole).toHaveBeenCalledWith(ROL_RESUELVE_PROMOCION);
    });

    it('DENIEGA al Desarrollador de APIs aunque sea gestor de partners', () => {
      // Este es el control real: si el Desarrollador de APIs pudiera resolver,
      // la aprobación humana dejaría de existir como separación de actores.
      // Arrange — gestiona partners, pero no es Administrador
      authApi.isAuthenticated.and.returnValue(true);
      authApi.hasRole.and.callFake((rol: string) => rol !== ROL_RESUELVE_PROMOCION);

      // Act
      const resultado = ejecutar(administradorPromocionGuard);

      // Assert
      expect(resultado).toEqual(router.createUrlTree(DENEGADO));
    });

    it('deniega al propio partner: nadie se aprueba a sí mismo', () => {
      // Arrange
      authApi.isAuthenticated.and.returnValue(true);
      authApi.hasRole.and.returnValue(false);

      // Act / Assert
      expect(ejecutar(administradorPromocionGuard)).toEqual(router.createUrlTree(DENEGADO));
    });

    it('usa hasRole y no hasAnyRole: el permiso no admite lista de roles', () => {
      // Arrange
      authApi.isAuthenticated.and.returnValue(true);
      authApi.hasRole.and.returnValue(true);

      // Act
      ejecutar(administradorPromocionGuard);

      // Assert
      expect(authApi.hasAnyRole).not.toHaveBeenCalled();
    });
  });

  describe('partnerIntegracionGuard', () => {
    it('permite al partner de integración', () => {
      // Arrange
      authApi.isAuthenticated.and.returnValue(true);
      authApi.hasRole.and.returnValue(true);

      // Act / Assert
      expect(ejecutar(partnerIntegracionGuard)).toBeTrue();
      expect(authApi.hasRole).toHaveBeenCalledWith(ROL_PARTNER_INTEGRACION);
    });

    it('deniega al gestor: el portal no es su superficie', () => {
      // Consola y portal son departamentos distintos y no se fusionan.
      // Arrange
      authApi.isAuthenticated.and.returnValue(true);
      authApi.hasRole.and.returnValue(false);

      // Act / Assert
      expect(ejecutar(partnerIntegracionGuard)).toEqual(router.createUrlTree(DENEGADO));
    });

    it('redirige a login si no hay sesión', () => {
      // Arrange
      authApi.isAuthenticated.and.returnValue(false);

      // Act / Assert
      expect(ejecutar(partnerIntegracionGuard)).toEqual(router.createUrlTree(LOGIN));
    });
  });
});
