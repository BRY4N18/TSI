/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import {
  informesCatalogoGuard,
  informesFinanzasGuard,
  listadosVisiblesPara,
} from './informes-suscripciones.guard';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

function ejecutar(guard: typeof informesCatalogoGuard, roles: string[]) {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      {
        provide: AuthApiService,
        useValue: { isAuthenticated: () => true, hasRole: (r: string) => roles.includes(r) },
      },
    ],
  });
  return TestBed.runInInjectionContext(() => guard({} as never, {} as never)) as
    | boolean
    | UrlTree;
}

describe('Guards de informes de Suscripciones', () => {
  describe('las dos autoridades no se mezclan', () => {
    it('estrategia_when_entra_a_catalogo_pasa', () => {
      expect(ejecutar(informesCatalogoGuard, ['DirectorEstrategia'])).toBeTrue();
    });

    it('estrategia_when_entra_a_finanzas_NO_pasa', () => {
      // ⚠️ El resultado económico no es materia de Estrategia. Un guard único
      // con la unión le daría el área del otro director.
      expect(ejecutar(informesFinanzasGuard, ['DirectorEstrategia'])).not.toBeTrue();
    });

    it('financiero_when_entra_a_finanzas_pasa', () => {
      expect(ejecutar(informesFinanzasGuard, ['DirectorFinanciero'])).toBeTrue();
    });

    it('financiero_when_entra_a_catalogo_NO_pasa', () => {
      expect(ejecutar(informesCatalogoGuard, ['DirectorFinanciero'])).not.toBeTrue();
    });

    it('administrador_when_entra_pasa_a_los_dos', () => {
      expect(ejecutar(informesCatalogoGuard, ['Administrador'])).toBeTrue();
      expect(ejecutar(informesFinanzasGuard, ['Administrador'])).toBeTrue();
    });
  });

  describe('los roles de cuenta', () => {
    for (const rol of ['Cliente', 'Proveedor']) {
      it(`${rol}_when_entra_pasa_a_los_cuatro`, () => {
        // Entran, y el backend los acota a su cuenta. Un cliente necesita ver su
        // propia deuda, y ahí es donde más importa que la vea.
        expect(ejecutar(informesCatalogoGuard, [rol])).toBeTrue();
        expect(ejecutar(informesFinanzasGuard, [rol])).toBeTrue();
      });
    }

    it('rol_ajeno_when_entra_no_pasa', () => {
      expect(ejecutar(informesCatalogoGuard, ['Operador'])).not.toBeTrue();
      expect(ejecutar(informesFinanzasGuard, ['Operador'])).not.toBeTrue();
    });
  });

  describe('el indice ofrece solo lo que el guard permite', () => {
    it('estrategia_when_mira_el_indice_no_ve_los_de_finanzas', () => {
      const visibles = listadosVisiblesPara((r) => r === 'DirectorEstrategia');

      expect(visibles).toContain('suscripciones');
      expect(visibles).toContain('solicitudes-cambio-plan');
      expect(visibles).not.toContain('facturas');
      expect(visibles).not.toContain('metodos-pago');
    });

    it('financiero_when_mira_el_indice_solo_ve_los_de_finanzas', () => {
      const visibles = listadosVisiblesPara((r) => r === 'DirectorFinanciero');

      expect(visibles).toEqual(['facturas', 'metodos-pago']);
    });

    it('cliente_when_mira_el_indice_ve_los_cuatro', () => {
      expect(listadosVisiblesPara((r) => r === 'Cliente').length).toBe(4);
    });
  });
});
