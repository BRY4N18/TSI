/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import {
  ROLES_CRECIMIENTO,
  ROLES_VALIDACION,
  gestionCrecimientoGuard,
  gestionValidacionGuard,
} from './red-operativa-gestion.guard';

function authStub(roles: string[], autenticado = true) {
  return {
    isAuthenticated: () => autenticado,
    hasRole: (rol: string) => roles.includes(rol),
  };
}

function ejecutar(
  guard: typeof gestionCrecimientoGuard,
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
  return TestBed.runInInjectionContext(() =>
    guard({} as never, {} as never),
  ) as boolean | UrlTree;
}

describe('guards de gestión de Red Operativa', () => {
  it('roles_when_se_declaran_no_son_una_union', () => {
    // El `Administrador` opera y no lee gestión (2026-08-19).
    expect([...ROLES_CRECIMIENTO]).toEqual(['DirectorExpansion']);
    expect([...ROLES_VALIDACION]).toEqual(['DirectorTecnologico']);
    expect((ROLES_CRECIMIENTO as readonly string[]).includes('DirectorTecnologico')).toBeFalse();
    expect((ROLES_VALIDACION as readonly string[]).includes('DirectorExpansion')).toBeFalse();
  });

  it('expansion_when_entra_a_crecimiento_pasa', () => {
    expect(ejecutar(gestionCrecimientoGuard, ['DirectorExpansion'])).toBeTrue();
  });

  it('expansion_when_entra_a_validacion_es_denegado', () => {
    const resultado = ejecutar(gestionValidacionGuard, ['DirectorExpansion']);
    expect(resultado instanceof UrlTree).toBeTrue();
    expect(String(resultado)).toContain('access-denied');
  });

  it('tecnologico_when_entra_a_validacion_pasa', () => {
    expect(ejecutar(gestionValidacionGuard, ['DirectorTecnologico'])).toBeTrue();
  });

  it('tecnologico_when_entra_a_crecimiento_es_denegado', () => {
    const resultado = ejecutar(gestionCrecimientoGuard, ['DirectorTecnologico']);
    expect(resultado instanceof UrlTree).toBeTrue();
    expect(String(resultado)).toContain('access-denied');
  });

  it('administrador_when_entra_ya_no_pasa_ninguna', () => {
    // ⚠️ Ya no salta el reparto por materia: era el único rol que lo hacía.
    const resultadoAdmin = ejecutar(gestionCrecimientoGuard, ['Administrador']);
    expect(resultadoAdmin instanceof UrlTree).toBeTrue();
    expect(String(resultadoAdmin)).toContain('access-denied');
    const resultadoAdminB = ejecutar(gestionValidacionGuard, ['Administrador']);
    expect(resultadoAdminB instanceof UrlTree).toBeTrue();
    expect(String(resultadoAdminB)).toContain('access-denied');
  });

  it('cliente_proveedor_y_operador_when_entran_son_denegados', () => {
    for (const rol of ['Cliente', 'Proveedor', 'Operador']) {
      expect(ejecutar(gestionCrecimientoGuard, [rol]) instanceof UrlTree).toBeTrue();
      expect(ejecutar(gestionValidacionGuard, [rol]) instanceof UrlTree).toBeTrue();
    }
  });

  it('sin_autenticar_when_entra_va_al_login', () => {
    expect(String(ejecutar(gestionCrecimientoGuard, [], false))).toContain('login');
  });
});
