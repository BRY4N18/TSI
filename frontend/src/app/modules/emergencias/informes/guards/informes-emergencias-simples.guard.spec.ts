/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import {
  ROLES_CLIENTE_EMERGENCIAS,
  ROLES_INTERNOS_EMERGENCIAS,
  informesCasosGuard,
  informesEmergenciasInternoGuard,
} from './informes-emergencias-simples.guard';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

function ejecutar(guard: typeof informesCasosGuard, roles: string[]) {
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

describe('Guards de informes simples de Emergencias', () => {
  it('roles_when_se_declaran_coinciden_con_el_permiso_del_backend', () => {
    expect(ROLES_INTERNOS_EMERGENCIAS.sort()).toEqual(
      ['Administrador', 'DirectorOperaciones', 'Operador', 'Tecnico'].sort(),
    );
    expect(ROLES_CLIENTE_EMERGENCIAS).toEqual(['Cliente']);
  });

  describe('el Partner de integracion no entra a ninguno', () => {
    it('partner_when_entra_a_casos_NO_pasa', () => {
      // ⚠️ Su acceso a los datos de siniestralidad tiene su propio camino, con
      // su alcance y su auditoría. Dejarlo entrar aquí duplicaría ese control
      // con otro que no lo audita.
      expect(ejecutar(informesCasosGuard, ['PartnerIntegracion'])).not.toBeTrue();
    });

    it('partner_when_entra_a_los_internos_NO_pasa', () => {
      expect(
        ejecutar(informesEmergenciasInternoGuard, ['PartnerIntegracion']),
      ).not.toBeTrue();
    });
  });

  describe('el Cliente solo entra a casos', () => {
    it('cliente_when_entra_a_casos_pasa', () => {
      // Entra, y el backend lo acota a los cerrados de sus zonas. El guard no
      // decide eso.
      expect(ejecutar(informesCasosGuard, ['Cliente'])).toBeTrue();
    });

    it('cliente_when_entra_a_los_otros_cuatro_NO_pasa', () => {
      const resultado = ejecutar(informesEmergenciasInternoGuard, ['Cliente']);

      expect(resultado).not.toBeTrue();
      expect(String(resultado)).toContain('access-denied');
    });
  });

  describe('los roles internos', () => {
    for (const rol of ['Operador', 'Tecnico', 'Administrador', 'DirectorOperaciones']) {
      it(`${rol}_when_entra_pasa_a_los_cinco`, () => {
        expect(ejecutar(informesCasosGuard, [rol])).toBeTrue();
        expect(ejecutar(informesEmergenciasInternoGuard, [rol])).toBeTrue();
      });
    }
  });

  it('los_dos_guards_when_se_comparan_no_son_el_mismo', () => {
    expect(informesCasosGuard).not.toBe(informesEmergenciasInternoGuard);
  });
});
