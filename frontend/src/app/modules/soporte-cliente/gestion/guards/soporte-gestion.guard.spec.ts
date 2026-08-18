/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { ROLES_GESTION_SOPORTE, soporteGestionGuard } from './soporte-gestion.guard';

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
    soporteGestionGuard({} as never, {} as never),
  ) as boolean | UrlTree;
}

describe('soporteGestionGuard', () => {
  it('roles_when_se_declaran_no_incluyen_cliente_ni_dev', () => {
    expect([...ROLES_GESTION_SOPORTE]).toEqual([
      'GerenteExitoCliente',
      'Soporte',
      'Administrador',
    ]);
    expect((ROLES_GESTION_SOPORTE as readonly string[]).includes('Cliente')).toBeFalse();
    expect((ROLES_GESTION_SOPORTE as readonly string[]).includes('DesarrolladorAPIs')).toBeFalse();
    expect((ROLES_GESTION_SOPORTE as readonly string[]).includes('DirectorTecnologico')).toBeFalse();
  });

  it('gerente_agente_y_admin_when_entran_pasan', () => {
    expect(ejecutar(['GerenteExitoCliente'])).toBeTrue();
    expect(ejecutar(['Soporte'])).toBeTrue();
    expect(ejecutar(['Administrador'])).toBeTrue();
  });

  it('cliente_operador_dev_y_director_tec_when_entran_son_denegados', () => {
    for (const rol of ['Cliente', 'Operador', 'DesarrolladorAPIs', 'DirectorTecnologico']) {
      const resultado = ejecutar([rol]);
      expect(resultado instanceof UrlTree).toBeTrue();
      expect(String(resultado)).toContain('access-denied');
    }
  });

  it('sin_autenticar_when_entra_va_al_login', () => {
    expect(String(ejecutar([], false))).toContain('login');
  });
});
