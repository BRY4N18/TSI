/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import {
  ROLES_CAPTACION,
  ROLES_CARTERA,
  ROLES_CICLO,
  ROLES_INGRESO,
  oe1CaptacionGuard,
  oe1CarteraGuard,
  oe1CicloGuard,
  oe1IngresoGuard,
} from './oe1.guard';

function authStub(roles: string[], autenticado = true) {
  return {
    isAuthenticated: () => autenticado,
    hasRole: (rol: string) => roles.includes(rol),
  };
}

function ejecutar(guard: typeof oe1IngresoGuard, roles: string[], autenticado = true) {
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

describe('guards OE1', () => {
  it('cuatro_listas_sin_union', () => {
    expect([...ROLES_INGRESO]).toEqual(['DirectorFinanciero', 'Gerente']);
    expect([...ROLES_CARTERA]).toEqual(['DirectorEstrategia', 'Gerente']);
    expect([...ROLES_CAPTACION]).toEqual(['DirectorMarketing', 'Gerente']);
    expect([...ROLES_CICLO]).toEqual(['Gerente']);
    expect((ROLES_INGRESO as readonly string[]).includes('DirectorMarketing')).toBeFalse();
    expect((ROLES_CICLO as readonly string[]).includes('DirectorFinanciero')).toBeFalse();
    expect((ROLES_INGRESO as readonly string[]).includes('Administrador')).toBeFalse();
    expect((ROLES_INGRESO as readonly string[]).includes('PartnerIntegracion')).toBeFalse();
    expect((ROLES_INGRESO as readonly string[]).includes('DirectorExpansion')).toBeFalse();
  });

  it('gerente_pasa_las_cuatro', () => {
    expect(ejecutar(oe1IngresoGuard, ['Gerente'])).toBeTrue();
    expect(ejecutar(oe1CarteraGuard, ['Gerente'])).toBeTrue();
    expect(ejecutar(oe1CaptacionGuard, ['Gerente'])).toBeTrue();
    expect(ejecutar(oe1CicloGuard, ['Gerente'])).toBeTrue();
  });

  it('financiero_solo_ingreso', () => {
    expect(ejecutar(oe1IngresoGuard, ['DirectorFinanciero'])).toBeTrue();
    expect(ejecutar(oe1CarteraGuard, ['DirectorFinanciero']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe1CaptacionGuard, ['DirectorFinanciero']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe1CicloGuard, ['DirectorFinanciero']) instanceof UrlTree).toBeTrue();
  });

  it('estrategia_solo_cartera', () => {
    expect(ejecutar(oe1CarteraGuard, ['DirectorEstrategia'])).toBeTrue();
    expect(ejecutar(oe1IngresoGuard, ['DirectorEstrategia']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe1CaptacionGuard, ['DirectorEstrategia']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe1CicloGuard, ['DirectorEstrategia']) instanceof UrlTree).toBeTrue();
  });

  it('marketing_solo_captacion', () => {
    expect(ejecutar(oe1CaptacionGuard, ['DirectorMarketing'])).toBeTrue();
    expect(ejecutar(oe1IngresoGuard, ['DirectorMarketing']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe1CarteraGuard, ['DirectorMarketing']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe1CicloGuard, ['DirectorMarketing']) instanceof UrlTree).toBeTrue();
  });

  it('partner_operador_denegados', () => {
    for (const rol of ['PartnerIntegracion', 'Operador', 'Administrador']) {
      expect(ejecutar(oe1IngresoGuard, [rol]) instanceof UrlTree).toBeTrue();
      expect(ejecutar(oe1CicloGuard, [rol]) instanceof UrlTree).toBeTrue();
    }
  });

  it('sin_autenticar_va_al_login', () => {
    expect(String(ejecutar(oe1IngresoGuard, [], false))).toContain('login');
  });
});
