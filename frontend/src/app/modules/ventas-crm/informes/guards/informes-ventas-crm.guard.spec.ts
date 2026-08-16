/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import {
  informesReasignacionesGuard,
  informesVentasGuard,
  listadosVisiblesPara,
} from './informes-ventas-crm.guard';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

function ejecutar(guard: typeof informesVentasGuard, roles: string[]) {
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

describe('Guards de informes de Ventas y CRM', () => {
  describe('las reasignaciones son supervision pura', () => {
    it('gerente_when_entra_a_prospectos_pasa', () => {
      // Entra, y el backend lo acota a su propia cartera.
      expect(ejecutar(informesVentasGuard, ['GerenteVentas'])).toBeTrue();
    });

    it('gerente_when_entra_a_reasignaciones_NO_pasa', () => {
      // ⚠️ El reparto de cartera es decisión de jefatura, no herramienta del
      // gerente cuya cartera se reparte.
      expect(ejecutar(informesReasignacionesGuard, ['GerenteVentas'])).not.toBeTrue();
    });

    it('gerente_de_cuentas_publicas_when_entra_recibe_el_mismo_trato', () => {
      expect(ejecutar(informesVentasGuard, ['GerenteCuentasPublicas'])).toBeTrue();
      expect(
        ejecutar(informesReasignacionesGuard, ['GerenteCuentasPublicas']),
      ).not.toBeTrue();
    });

    it('marketing_when_entra_pasa_a_los_cuatro', () => {
      // Es la autoridad del departamento.
      expect(ejecutar(informesVentasGuard, ['DirectorMarketing'])).toBeTrue();
      expect(ejecutar(informesReasignacionesGuard, ['DirectorMarketing'])).toBeTrue();
    });

    it('rol_ajeno_when_entra_no_pasa', () => {
      expect(ejecutar(informesVentasGuard, ['Operador'])).not.toBeTrue();
    });
  });

  describe('el indice ofrece solo lo que el guard permite', () => {
    it('gerente_when_mira_el_indice_no_ve_reasignaciones', () => {
      const visibles = listadosVisiblesPara((r) => r === 'GerenteVentas');

      expect(visibles).toContain('prospectos');
      expect(visibles).not.toContain('reasignaciones');
    });

    it('administrador_when_mira_el_indice_ve_los_cuatro', () => {
      expect(listadosVisiblesPara((r) => r === 'Administrador').length).toBe(4);
    });
  });
});
