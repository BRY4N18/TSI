/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import {
  ROLES_CALIDAD,
  ROLES_COBERTURA,
  ROLES_CONCENTRACION,
  ROLES_IMPACTO,
  oe4CalidadGuard,
  oe4CoberturaGuard,
  oe4ConcentracionGuard,
  oe4ImpactoGuard,
} from './oe4.guard';

function authStub(roles: string[], autenticado = true) {
  return {
    isAuthenticated: () => autenticado,
    hasRole: (rol: string) => roles.includes(rol),
  };
}

function ejecutar(guard: typeof oe4CalidadGuard, roles: string[], autenticado = true) {
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

describe('guards OE4', () => {
  it('cuatro_listas_sin_union_ni_partner', () => {
    expect([...ROLES_CALIDAD]).toEqual(['DirectorDatos', 'DirectorOperaciones', 'Gerente']);
    expect([...ROLES_CONCENTRACION]).toEqual(['DirectorDatos', 'Gerente']);
    expect([...ROLES_IMPACTO]).toEqual(['DirectorDatos', 'DirectorOperaciones', 'Gerente']);
    expect([...ROLES_COBERTURA]).toEqual(['DirectorDatos', 'Gerente']);
    expect((ROLES_CONCENTRACION as readonly string[]).includes('DirectorOperaciones')).toBeFalse();
    expect((ROLES_CALIDAD as readonly string[]).includes('PartnerIntegracion')).toBeFalse();
  });

  it('gerente_y_datos_pasan_las_cuatro', () => {
    for (const rol of ['Gerente', 'DirectorDatos']) {
      expect(ejecutar(oe4CalidadGuard, [rol])).toBeTrue();
      expect(ejecutar(oe4ConcentracionGuard, [rol])).toBeTrue();
      expect(ejecutar(oe4ImpactoGuard, [rol])).toBeTrue();
      expect(ejecutar(oe4CoberturaGuard, [rol])).toBeTrue();
    }
  });

  it('operaciones_pasa_calidad_impacto_falla_concentracion_cobertura', () => {
    expect(ejecutar(oe4CalidadGuard, ['DirectorOperaciones'])).toBeTrue();
    expect(ejecutar(oe4ImpactoGuard, ['DirectorOperaciones'])).toBeTrue();
    expect(ejecutar(oe4ConcentracionGuard, ['DirectorOperaciones']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe4CoberturaGuard, ['DirectorOperaciones']) instanceof UrlTree).toBeTrue();
  });

  it('partner_tecnologico_expansion_fallan', () => {
    for (const rol of ['PartnerIntegracion', 'DirectorTecnologico', 'DirectorExpansion']) {
      expect(ejecutar(oe4CalidadGuard, [rol]) instanceof UrlTree).toBeTrue();
    }
  });

  it('sin_autenticar_va_al_login', () => {
    expect(String(ejecutar(oe4CalidadGuard, [], false))).toContain('login');
  });
});
