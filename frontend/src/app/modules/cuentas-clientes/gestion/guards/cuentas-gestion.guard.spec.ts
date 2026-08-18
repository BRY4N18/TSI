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
    expect([...ROLES_CICLO]).toEqual(['Administrador']);
    expect([...ROLES_INCORPORACION]).toEqual(['Administrador']);
    expect([...ROLES_ACCESO]).toEqual(['DirectorTecnologico', 'Administrador']);
    expect((ROLES_CICLO as readonly string[]).includes('DirectorTecnologico')).toBeFalse();
    expect((ROLES_INCORPORACION as readonly string[]).includes('DirectorTecnologico')).toBeFalse();
  });

  it('administrador_when_entra_pasa_las_tres', () => {
    expect(ejecutar(gestionCicloGuard, ['Administrador'])).toBeTrue();
    expect(ejecutar(gestionIncorporacionGuard, ['Administrador'])).toBeTrue();
    expect(ejecutar(gestionAccesoGuard, ['Administrador'])).toBeTrue();
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
