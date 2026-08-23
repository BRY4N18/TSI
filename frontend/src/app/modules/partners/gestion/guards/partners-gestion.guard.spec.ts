/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { ROLES_GESTION_PARTNERS, partnersGestionGuard } from './partners-gestion.guard';

function authStub(roles: string[], autenticado = true) {
  return {
    isAuthenticated: () => autenticado,
    hasRole: (rol: string) => roles.includes(rol),
  };
}

function ejecutar(roles: string[], autenticado = true) {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      { provide: AuthApiService, useValue: authStub(roles, autenticado) },
    ],
  });
  return TestBed.runInInjectionContext(() =>
    partnersGestionGuard({} as never, {} as never),
  ) as boolean | UrlTree;
}

describe('partnersGestionGuard', () => {
  it('roles_when_se_declaran_son_director_y_admin', () => {
    // El `Administrador` opera y no lee gestión (2026-08-19).
    expect([...ROLES_GESTION_PARTNERS]).toEqual(['DirectorTecnologico']);
    expect((ROLES_GESTION_PARTNERS as readonly string[]).includes('PartnerIntegracion')).toBeFalse();
    expect((ROLES_GESTION_PARTNERS as readonly string[]).includes('DesarrolladorAPIs')).toBeFalse();
  });

  it('director_tecnologico_when_entra_pasa', () => {
    expect(ejecutar(['DirectorTecnologico'])).toBeTrue();
  });

  it('administrador_when_entra_ya_no_pasa', () => {
    const resultadoAdmin = ejecutar(['Administrador']);
    expect(resultadoAdmin instanceof UrlTree).toBeTrue();
    expect(String(resultadoAdmin)).toContain('access-denied');
  });

  it('partner_desarrollador_operador_y_cliente_when_entran_son_denegados', () => {
    for (const rol of ['PartnerIntegracion', 'DesarrolladorAPIs', 'Operador', 'Cliente']) {
      const resultado = ejecutar([rol]);
      expect(resultado instanceof UrlTree).toBeTrue();
      expect(String(resultado)).toContain('access-denied');
    }
  });

  it('sin_autenticar_when_entra_va_al_login', () => {
    expect(String(ejecutar([], false))).toContain('login');
  });
});
