/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import { ROLES_OE6, oe6Guard } from './oe6.guard';

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
  return TestBed.runInInjectionContext(() => oe6Guard({} as never, {} as never)) as
    | boolean
    | UrlTree;
}

describe('guard OE6', () => {
  it('roles_operaciones_y_gerente', () => {
    expect([...ROLES_OE6]).toEqual(['DirectorOperaciones', 'Gerente']);
    expect((ROLES_OE6 as readonly string[]).includes('DirectorFinanciero')).toBeFalse();
    expect((ROLES_OE6 as readonly string[]).includes('GerenteExitoCliente')).toBeFalse();
    expect((ROLES_OE6 as readonly string[]).includes('PartnerIntegracion')).toBeFalse();
    expect((ROLES_OE6 as readonly string[]).includes('Administrador')).toBeFalse();
  });

  it('operaciones_y_gerente_pasan', () => {
    expect(ejecutar(['DirectorOperaciones'])).toBeTrue();
    expect(ejecutar(['Gerente'])).toBeTrue();
  });

  it('financiero_exito_partner_denegados', () => {
    for (const rol of [
      'DirectorFinanciero',
      'GerenteExitoCliente',
      'PartnerIntegracion',
      'Operador',
      'Administrador',
    ]) {
      expect(ejecutar([rol]) instanceof UrlTree).toBeTrue();
    }
  });

  it('sin_autenticar_va_al_login', () => {
    expect(String(ejecutar([], false))).toContain('login');
  });
});
