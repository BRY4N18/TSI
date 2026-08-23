/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import {
  ROLES_CALIDAD,
  ROLES_CAPACIDAD,
  ROLES_LATENCIA,
  ROLES_RESPALDO,
  oe3CalidadGuard,
  oe3CapacidadGuard,
  oe3LatenciaGuard,
  oe3RespaldoGuard,
} from './oe3.guard';

function authStub(roles: string[], autenticado = true) {
  return {
    isAuthenticated: () => autenticado,
    hasRole: (rol: string) => roles.includes(rol),
  };
}

function ejecutar(
  guard: typeof oe3LatenciaGuard,
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

describe('guards OE3', () => {
  it('cuatro_listas_sin_union_ni_tecnologico', () => {
    expect([...ROLES_LATENCIA]).toEqual(['DirectorOperaciones', 'Gerente']);
    expect([...ROLES_CALIDAD]).toEqual(['DirectorOperaciones', 'Gerente']);
    expect([...ROLES_CAPACIDAD]).toEqual([
      'DirectorExpansion',
      'DirectorOperaciones',
      'Gerente',
    ]);
    expect([...ROLES_RESPALDO]).toEqual(['DirectorExpansion', 'Gerente']);
    expect((ROLES_LATENCIA as readonly string[]).includes('DirectorExpansion')).toBeFalse();
    expect((ROLES_RESPALDO as readonly string[]).includes('DirectorOperaciones')).toBeFalse();
    expect((ROLES_LATENCIA as readonly string[]).includes('DirectorTecnologico')).toBeFalse();
    expect((ROLES_CAPACIDAD as readonly string[]).includes('Administrador')).toBeFalse();
    expect((ROLES_LATENCIA as readonly string[]).includes('PartnerIntegracion')).toBeFalse();
    expect((ROLES_LATENCIA as readonly string[]).includes('DirectorFinanciero')).toBeFalse();
  });

  it('gerente_pasa_las_cuatro', () => {
    expect(ejecutar(oe3LatenciaGuard, ['Gerente'])).toBeTrue();
    expect(ejecutar(oe3CalidadGuard, ['Gerente'])).toBeTrue();
    expect(ejecutar(oe3CapacidadGuard, ['Gerente'])).toBeTrue();
    expect(ejecutar(oe3RespaldoGuard, ['Gerente'])).toBeTrue();
  });

  it('operaciones_pasa_latencia_calidad_capacidad_falla_respaldo', () => {
    expect(ejecutar(oe3LatenciaGuard, ['DirectorOperaciones'])).toBeTrue();
    expect(ejecutar(oe3CalidadGuard, ['DirectorOperaciones'])).toBeTrue();
    expect(ejecutar(oe3CapacidadGuard, ['DirectorOperaciones'])).toBeTrue();
    expect(ejecutar(oe3RespaldoGuard, ['DirectorOperaciones']) instanceof UrlTree).toBeTrue();
  });

  it('expansion_pasa_capacidad_respaldo_falla_latencia_calidad', () => {
    expect(ejecutar(oe3CapacidadGuard, ['DirectorExpansion'])).toBeTrue();
    expect(ejecutar(oe3RespaldoGuard, ['DirectorExpansion'])).toBeTrue();
    expect(ejecutar(oe3LatenciaGuard, ['DirectorExpansion']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe3CalidadGuard, ['DirectorExpansion']) instanceof UrlTree).toBeTrue();
  });

  it('tecnologico_financiero_partner_operador_fallan_las_cuatro', () => {
    for (const rol of [
      'DirectorTecnologico',
      'DirectorFinanciero',
      'PartnerIntegracion',
      'Operador',
      'Administrador',
    ]) {
      expect(ejecutar(oe3LatenciaGuard, [rol]) instanceof UrlTree).toBeTrue();
      expect(ejecutar(oe3CalidadGuard, [rol]) instanceof UrlTree).toBeTrue();
      expect(ejecutar(oe3CapacidadGuard, [rol]) instanceof UrlTree).toBeTrue();
      expect(ejecutar(oe3RespaldoGuard, [rol]) instanceof UrlTree).toBeTrue();
    }
  });

  it('sin_autenticar_va_al_login', () => {
    expect(String(ejecutar(oe3LatenciaGuard, [], false))).toContain('login');
  });
});
