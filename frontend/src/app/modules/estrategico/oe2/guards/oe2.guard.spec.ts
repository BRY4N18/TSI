/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import {
  ROLES_DINERO,
  ROLES_USO_ECOSISTEMA,
  oe2DineroGuard,
  oe2UsoEcosistemaGuard,
} from './oe2.guard';

function authStub(roles: string[], autenticado = true) {
  return {
    isAuthenticated: () => autenticado,
    hasRole: (rol: string) => roles.includes(rol),
  };
}

function ejecutar(guard: typeof oe2DineroGuard, roles: string[], autenticado = true) {
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

describe('guards OE2', () => {
  it('roles_no_son_una_union_en_uso', () => {
    expect([...ROLES_USO_ECOSISTEMA]).toEqual(['DirectorTecnologico', 'Gerente']);
    expect((ROLES_USO_ECOSISTEMA as readonly string[]).includes('DirectorFinanciero')).toBeFalse();
    expect((ROLES_USO_ECOSISTEMA as readonly string[]).includes('Administrador')).toBeFalse();
    expect((ROLES_DINERO as readonly string[]).includes('DirectorFinanciero')).toBeTrue();
  });

  it('tecnologico_y_gerente_pasan_uso_y_dinero', () => {
    for (const rol of ['DirectorTecnologico', 'Gerente']) {
      expect(ejecutar(oe2UsoEcosistemaGuard, [rol])).toBeTrue();
      expect(ejecutar(oe2DineroGuard, [rol])).toBeTrue();
    }
  });

  it('financiero_pasa_dinero_y_falla_uso', () => {
    expect(ejecutar(oe2DineroGuard, ['DirectorFinanciero'])).toBeTrue();
    expect(ejecutar(oe2UsoEcosistemaGuard, ['DirectorFinanciero']) instanceof UrlTree).toBeTrue();
  });

  it('partner_y_operador_denegados', () => {
    for (const rol of ['PartnerIntegracion', 'Operador', 'Administrador']) {
      expect(ejecutar(oe2UsoEcosistemaGuard, [rol]) instanceof UrlTree).toBeTrue();
      expect(ejecutar(oe2DineroGuard, [rol]) instanceof UrlTree).toBeTrue();
    }
  });

  it('sin_autenticar_va_al_login', () => {
    expect(String(ejecutar(oe2UsoEcosistemaGuard, [], false))).toContain('login');
  });
});
