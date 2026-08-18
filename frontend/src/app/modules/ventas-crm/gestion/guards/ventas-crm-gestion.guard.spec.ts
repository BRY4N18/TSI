/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import {
  ROLES_GESTION_VENTAS_CRM,
  ventasCrmGestionGuard,
} from './ventas-crm-gestion.guard';

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
    ventasCrmGestionGuard({} as never, {} as never),
  ) as boolean | UrlTree;
}

describe('ventasCrmGestionGuard', () => {
  it('roles_when_se_declaran_no_incluyen_cuentas_publicas', () => {
    expect([...ROLES_GESTION_VENTAS_CRM]).toEqual([
      'DirectorMarketing',
      'GerenteVentas',
      'Administrador',
    ]);
    expect((ROLES_GESTION_VENTAS_CRM as readonly string[]).includes('GerenteCuentasPublicas')).toBeFalse();
  });

  it('director_gerente_y_admin_when_entran_pasan', () => {
    expect(ejecutar(['DirectorMarketing'])).toBeTrue();
    expect(ejecutar(['GerenteVentas'])).toBeTrue();
    expect(ejecutar(['Administrador'])).toBeTrue();
  });

  it('cuentas_publicas_operador_y_cliente_when_entran_son_denegados', () => {
    for (const rol of ['GerenteCuentasPublicas', 'Operador', 'Cliente']) {
      const resultado = ejecutar([rol]);
      expect(resultado instanceof UrlTree).toBeTrue();
      expect(String(resultado)).toContain('access-denied');
    }
  });

  it('sin_autenticar_when_entra_va_al_login', () => {
    expect(String(ejecutar([], false))).toContain('login');
  });
});
