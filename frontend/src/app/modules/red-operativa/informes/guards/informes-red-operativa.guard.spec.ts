/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import {
  informesFlotaGuard,
  informesRegionesGuard,
  informesValidacionesGuard,
  listadosVisiblesPara,
} from './informes-red-operativa.guard';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

function ejecutar(guard: typeof informesFlotaGuard, roles: string[]) {
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

describe('Guards de informes de Red Operativa', () => {
  describe('una region no pertenece a ninguna empresa de flota', () => {
    it('proveedor_when_entra_a_flota_pasa', () => {
      // Entra, y el backend lo acota a su propia flota.
      expect(ejecutar(informesFlotaGuard, ['Proveedor'])).toBeTrue();
    });

    it('proveedor_when_entra_a_regiones_NO_pasa', () => {
      // ⚠️ El estado de la red es materia de gobierno, no información que un
      // proveedor deba ver. Un guard único se la daría.
      expect(ejecutar(informesRegionesGuard, ['Proveedor'])).not.toBeTrue();
    });

    it('proveedor_when_entra_a_validaciones_NO_pasa', () => {
      expect(ejecutar(informesValidacionesGuard, ['Proveedor'])).not.toBeTrue();
    });
  });

  describe('las validaciones son solo del Tecnologico', () => {
    it('expansion_when_entra_a_regiones_pasa', () => {
      // Decide dónde crecer: necesita el estado de las regiones.
      expect(ejecutar(informesRegionesGuard, ['DirectorExpansion'])).toBeTrue();
    });

    it('expansion_when_entra_a_validaciones_NO_pasa', () => {
      // ⚠️ El detalle de por qué se rechaza una región no le sirve a quien
      // decide dónde crecer: lo fija el Tecnológico.
      expect(ejecutar(informesValidacionesGuard, ['DirectorExpansion'])).not.toBeTrue();
    });

    it('tecnologico_when_entra_a_validaciones_pasa', () => {
      expect(ejecutar(informesValidacionesGuard, ['DirectorTecnologico'])).toBeTrue();
    });

    it('tecnologico_when_entra_a_flota_NO_pasa', () => {
      // La flota es de Expansión y de las cuentas proveedoras.
      expect(ejecutar(informesFlotaGuard, ['DirectorTecnologico'])).not.toBeTrue();
    });
  });

  describe('el indice ofrece solo lo que el guard permite', () => {
    it('proveedor_when_mira_el_indice_solo_ve_flota_y_bajas', () => {
      expect(listadosVisiblesPara((r) => r === 'Proveedor')).toEqual([
        'flota',
        'bajas-unidad',
      ]);
    });

    it('expansion_when_mira_el_indice_no_ve_validaciones', () => {
      const visibles = listadosVisiblesPara((r) => r === 'DirectorExpansion');

      expect(visibles).toContain('regiones');
      expect(visibles).not.toContain('validaciones-region');
    });

    it('tecnologico_when_mira_el_indice_ve_regiones_y_validaciones', () => {
      expect(listadosVisiblesPara((r) => r === 'DirectorTecnologico')).toEqual([
        'regiones',
        'validaciones-region',
      ]);
    });

    it('administrador_when_mira_el_indice_ve_los_cuatro', () => {
      expect(listadosVisiblesPara((r) => r === 'Administrador').length).toBe(4);
    });
  });
});
