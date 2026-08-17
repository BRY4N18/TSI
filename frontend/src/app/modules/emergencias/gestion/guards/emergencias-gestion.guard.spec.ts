/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import {
  ROLES_GESTION_EMERGENCIAS,
  emergenciasGestionGuard,
} from './emergencias-gestion.guard';

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
    emergenciasGestionGuard({} as never, {} as never),
  ) as boolean | UrlTree;
}

describe('emergenciasGestionGuard', () => {
  it('roles_when_se_declaran_son_director_y_administrador', () => {
    expect([...ROLES_GESTION_EMERGENCIAS]).toEqual(['DirectorOperaciones', 'Administrador']);
  });

  it('director_when_entra_pasa', () => {
    expect(ejecutar(['DirectorOperaciones'])).toBeTrue();
  });

  it('administrador_when_entra_pasa', () => {
    expect(ejecutar(['Administrador'])).toBeTrue();
  });

  it('operador_when_entra_es_denegado', () => {
    const resultado = ejecutar(['Operador']);
    expect(resultado instanceof UrlTree).toBeTrue();
    expect(String(resultado)).toContain('access-denied');
  });

  it('cliente_when_entra_es_denegado', () => {
    expect(ejecutar(['Cliente']) instanceof UrlTree).toBeTrue();
  });

  it('partner_when_entra_es_denegado', () => {
    expect(ejecutar(['Partner']) instanceof UrlTree).toBeTrue();
  });

  it('sin_autenticar_when_entra_va_al_login', () => {
    expect(String(ejecutar([], false))).toContain('login');
  });
});
