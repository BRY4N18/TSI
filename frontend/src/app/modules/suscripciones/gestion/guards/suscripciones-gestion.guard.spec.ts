/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import {
  ROLES_CATALOGO,
  ROLES_FINANZAS,
  gestionCatalogoGuard,
  gestionFinanzasGuard,
} from './suscripciones-gestion.guard';

function authStub(roles: string[], autenticado = true) {
  return {
    isAuthenticated: () => autenticado,
    hasRole: (rol: string) => roles.includes(rol),
  };
}

function ejecutar(
  guard: typeof gestionFinanzasGuard,
  roles: string[],
  autenticado = true,
) {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      { provide: AuthApiService, useValue: authStub(roles, autenticado) },
    ],
  });
  return TestBed.runInInjectionContext(() => guard({} as never, {} as never)) as
    | boolean
    | UrlTree;
}

describe('guards de gestión de Suscripciones', () => {
  it('roles_when_se_declaran_no_son_una_union', () => {
    // El `Administrador` opera y no lee gestión (2026-08-19).
    expect([...ROLES_FINANZAS]).toEqual(['DirectorFinanciero']);
    expect([...ROLES_CATALOGO]).toEqual(['DirectorEstrategia']);
    expect((ROLES_FINANZAS as readonly string[]).includes('DirectorEstrategia')).toBeFalse();
    expect((ROLES_CATALOGO as readonly string[]).includes('DirectorFinanciero')).toBeFalse();
  });

  it('financiero_when_entra_a_finanzas_pasa', () => {
    expect(ejecutar(gestionFinanzasGuard, ['DirectorFinanciero'])).toBeTrue();
  });

  it('financiero_when_entra_a_catalogo_es_denegado', () => {
    const resultado = ejecutar(gestionCatalogoGuard, ['DirectorFinanciero']);
    expect(resultado instanceof UrlTree).toBeTrue();
    expect(String(resultado)).toContain('access-denied');
  });

  it('estrategia_when_entra_a_catalogo_pasa', () => {
    expect(ejecutar(gestionCatalogoGuard, ['DirectorEstrategia'])).toBeTrue();
  });

  it('estrategia_when_entra_a_finanzas_es_denegado', () => {
    const resultado = ejecutar(gestionFinanzasGuard, ['DirectorEstrategia']);
    expect(resultado instanceof UrlTree).toBeTrue();
    expect(String(resultado)).toContain('access-denied');
  });

  it('administrador_when_entra_ya_no_pasa_ninguna', () => {
    // ⚠️ Era el único rol que saltaba el reparto finanzas/catálogo entero.
    const resultadoAdmin = ejecutar(gestionFinanzasGuard, ['Administrador']);
    expect(resultadoAdmin instanceof UrlTree).toBeTrue();
    expect(String(resultadoAdmin)).toContain('access-denied');
    const resultadoAdminB = ejecutar(gestionCatalogoGuard, ['Administrador']);
    expect(resultadoAdminB instanceof UrlTree).toBeTrue();
    expect(String(resultadoAdminB)).toContain('access-denied');
  });

  it('cliente_proveedor_y_operador_when_entran_son_denegados', () => {
    for (const rol of ['Cliente', 'Proveedor', 'Operador']) {
      expect(ejecutar(gestionFinanzasGuard, [rol]) instanceof UrlTree).toBeTrue();
      expect(ejecutar(gestionCatalogoGuard, [rol]) instanceof UrlTree).toBeTrue();
    }
  });

  it('sin_autenticar_when_entra_va_al_login', () => {
    expect(String(ejecutar(gestionFinanzasGuard, [], false))).toContain('login');
  });
});
