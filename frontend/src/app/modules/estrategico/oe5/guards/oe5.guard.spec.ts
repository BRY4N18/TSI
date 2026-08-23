/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';
import {
  ROLES_INGRESOS,
  ROLES_PLANES,
  ROLES_RIESGO,
  ROLES_SERVICIO,
  oe5IngresosGuard,
  oe5PlanesGuard,
  oe5RiesgoGuard,
  oe5ServicioGuard,
} from './oe5.guard';

function authStub(roles: string[], autenticado = true) {
  return {
    isAuthenticated: () => autenticado,
    hasRole: (rol: string) => roles.includes(rol),
  };
}

function ejecutar(guard: typeof oe5ServicioGuard, roles: string[], autenticado = true) {
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

describe('guards OE5', () => {
  it('cuatro_listas_sin_union', () => {
    expect([...ROLES_SERVICIO]).toEqual(['GerenteExitoCliente', 'Gerente']);
    expect([...ROLES_INGRESOS]).toEqual(['DirectorFinanciero', 'Gerente']);
    expect([...ROLES_PLANES]).toEqual(['DirectorEstrategia', 'Gerente']);
    expect([...ROLES_RIESGO]).toEqual(['Gerente']);
    expect((ROLES_SERVICIO as readonly string[]).includes('DirectorFinanciero')).toBeFalse();
    expect((ROLES_RIESGO as readonly string[]).includes('GerenteExitoCliente')).toBeFalse();
    expect((ROLES_SERVICIO as readonly string[]).includes('Administrador')).toBeFalse();
    expect((ROLES_SERVICIO as readonly string[]).includes('PartnerIntegracion')).toBeFalse();
    expect((ROLES_SERVICIO as readonly string[]).includes('DirectorMarketing')).toBeFalse();
  });

  it('gerente_pasa_las_cuatro', () => {
    expect(ejecutar(oe5ServicioGuard, ['Gerente'])).toBeTrue();
    expect(ejecutar(oe5IngresosGuard, ['Gerente'])).toBeTrue();
    expect(ejecutar(oe5PlanesGuard, ['Gerente'])).toBeTrue();
    expect(ejecutar(oe5RiesgoGuard, ['Gerente'])).toBeTrue();
  });

  it('exito_cliente_solo_servicio', () => {
    expect(ejecutar(oe5ServicioGuard, ['GerenteExitoCliente'])).toBeTrue();
    expect(ejecutar(oe5IngresosGuard, ['GerenteExitoCliente']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe5PlanesGuard, ['GerenteExitoCliente']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe5RiesgoGuard, ['GerenteExitoCliente']) instanceof UrlTree).toBeTrue();
  });

  it('financiero_solo_ingresos', () => {
    expect(ejecutar(oe5IngresosGuard, ['DirectorFinanciero'])).toBeTrue();
    expect(ejecutar(oe5ServicioGuard, ['DirectorFinanciero']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe5PlanesGuard, ['DirectorFinanciero']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe5RiesgoGuard, ['DirectorFinanciero']) instanceof UrlTree).toBeTrue();
  });

  it('estrategia_solo_planes', () => {
    expect(ejecutar(oe5PlanesGuard, ['DirectorEstrategia'])).toBeTrue();
    expect(ejecutar(oe5ServicioGuard, ['DirectorEstrategia']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe5IngresosGuard, ['DirectorEstrategia']) instanceof UrlTree).toBeTrue();
    expect(ejecutar(oe5RiesgoGuard, ['DirectorEstrategia']) instanceof UrlTree).toBeTrue();
  });

  it('partner_operador_denegados', () => {
    for (const rol of ['PartnerIntegracion', 'Operador', 'Administrador']) {
      expect(ejecutar(oe5ServicioGuard, [rol]) instanceof UrlTree).toBeTrue();
      expect(ejecutar(oe5RiesgoGuard, [rol]) instanceof UrlTree).toBeTrue();
    }
  });

  it('sin_autenticar_va_al_login', () => {
    expect(String(ejecutar(oe5ServicioGuard, [], false))).toContain('login');
  });
});
