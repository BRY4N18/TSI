/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../auth/services/auth-api.service';
import {
  ROLES_ACCESO,
  ROLES_CICLO,
  ROLES_INCORPORACION,
  gestionAccesoGuard,
  gestionCicloGuard,
  gestionIncorporacionGuard,
} from './cuentas-gestion.guard';

function authStub(roles: string[], autenticado = true) {
  return {
    isAuthenticated: () => autenticado,
    hasRole: (rol: string) => roles.includes(rol),
  };
}

function ejecutar(
  guard: typeof gestionCicloGuard,
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

describe('guards de gestión de Cuentas', () => {
  it('roles_when_se_declaran_no_son_una_union', () => {
    // La autoridad quedó repartida el 2026-08-19: el Director de Cuentas
    // responde del ciclo y la incorporación; el Tecnológico, solo del acceso.
    expect([...ROLES_CICLO]).toEqual(['DirectorCuentas']);
    expect([...ROLES_INCORPORACION]).toEqual(['DirectorCuentas']);
    expect([...ROLES_ACCESO]).toEqual(['DirectorTecnologico']);
    expect((ROLES_CICLO as readonly string[]).includes('DirectorTecnologico')).toBeFalse();
    expect((ROLES_INCORPORACION as readonly string[]).includes('DirectorTecnologico')).toBeFalse();
  });

  it('administrador_when_entra_ya_no_pasa_ninguna', () => {
    // ⚠️ Entraba a las tres porque era la **única** forma de abrir siete de
    // estos informes: el departamento no tenía autoridad propia. Creado el
    // Director de Cuentas, deja de hacer falta y vuelve a su papel: operar.
    expect(ejecutar(gestionCicloGuard, ['Administrador']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(gestionIncorporacionGuard, ['Administrador']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(gestionAccesoGuard, ['Administrador']) instanceof UrlTree).toBeTrue();
  });

  it('cuentas_when_entra_pasa_ciclo_e_incorporacion_pero_no_acceso', () => {
    // El reparto en el otro sentido: quien responde de por qué se van los
    // clientes no fija los criterios técnicos de acceso.
    expect(ejecutar(gestionCicloGuard, ['DirectorCuentas'])).toBeTrue();
    expect(ejecutar(gestionIncorporacionGuard, ['DirectorCuentas'])).toBeTrue();
    expect(ejecutar(gestionAccesoGuard, ['DirectorCuentas']) instanceof UrlTree).toBeTrue();
  });

  it('tecnologico_when_entra_a_acceso_pasa_y_al_ciclo_es_denegado', () => {
    expect(ejecutar(gestionAccesoGuard, ['DirectorTecnologico'])).toBeTrue();
    expect(ejecutar(gestionCicloGuard, ['DirectorTecnologico']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(gestionIncorporacionGuard, ['DirectorTecnologico']) instanceof UrlTree).toBeTrue();
    expect(String(ejecutar(gestionCicloGuard, ['DirectorTecnologico']))).toContain('access-denied');
  });

  it('cliente_y_operador_when_entran_son_denegados', () => {
    for (const rol of ['Cliente', 'Operador']) {
      expect(ejecutar(gestionCicloGuard, [rol]) instanceof UrlTree).toBeTrue();
      expect(ejecutar(gestionAccesoGuard, [rol]) instanceof UrlTree).toBeTrue();
    }
  });

  it('sin_autenticar_when_entra_va_al_login', () => {
    expect(String(ejecutar(gestionCicloGuard, [], false))).toContain('login');
  });
});
