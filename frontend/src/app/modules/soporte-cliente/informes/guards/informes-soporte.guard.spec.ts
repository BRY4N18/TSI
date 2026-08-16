/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import {
  ROLES_INFORMES_ATENCION,
  ROLES_INFORMES_REPORTADORES,
  informesEscaladosGuard,
  informesTicketsGuard,
} from './informes-soporte.guard';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

function ejecutar(guard: typeof informesTicketsGuard, roles: string[]) {
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

describe('Guards de informes de Soporte al Cliente', () => {
  it('roles_when_se_declaran_coinciden_con_el_permiso_del_backend', () => {
    // `ROLES_ATENCION` y `ROLES_REPORTADORES` de `apps/soporte_cliente/permissions.py`.
    expect(ROLES_INFORMES_ATENCION.sort()).toEqual(
      [
        'Administrador',
        'DesarrolladorAPIs',
        'DirectorTecnologico',
        'GerenteExitoCliente',
        'Soporte',
      ].sort(),
    );
    expect(ROLES_INFORMES_REPORTADORES.sort()).toEqual(['Cliente', 'PartnerIntegracion'].sort());
  });

  describe('la asimetria del departamento', () => {
    it('cliente_when_entra_a_tickets_pasa', () => {
      // Entra, y el backend lo acota a los suyos. El guard no decide eso.
      expect(ejecutar(informesTicketsGuard, ['Cliente'])).toBeTrue();
    });

    it('cliente_when_entra_a_escalados_NO_pasa', () => {
      // ⚠️ Un escalado es proceso interno del equipo de atención. Un guard
      // único con la unión de roles se lo daría.
      expect(ejecutar(informesEscaladosGuard, ['Cliente'])).not.toBeTrue();
    });

    it('partner_when_entra_recibe_el_mismo_trato_que_el_cliente', () => {
      // El acotamiento no depende de «ser Cliente»: es la corrección que el
      // módulo operativo ya tuvo que hacer.
      expect(ejecutar(informesTicketsGuard, ['PartnerIntegracion'])).toBeTrue();
      expect(ejecutar(informesEscaladosGuard, ['PartnerIntegracion'])).not.toBeTrue();
    });

    it('agente_when_entra_pasa_a_los_dos', () => {
      expect(ejecutar(informesTicketsGuard, ['Soporte'])).toBeTrue();
      expect(ejecutar(informesEscaladosGuard, ['Soporte'])).toBeTrue();
    });

    it('gerente_exito_when_entra_pasa_a_los_dos', () => {
      // Es la autoridad del departamento, no `SupervisorSoporte` — que es el
      // destinatario operativo de un escalado automático.
      expect(ejecutar(informesTicketsGuard, ['GerenteExitoCliente'])).toBeTrue();
      expect(ejecutar(informesEscaladosGuard, ['GerenteExitoCliente'])).toBeTrue();
    });

    it('rol_ajeno_when_entra_no_pasa_a_ninguno', () => {
      expect(ejecutar(informesTicketsGuard, ['OperadorDespacho'])).not.toBeTrue();
      expect(ejecutar(informesEscaladosGuard, ['OperadorDespacho'])).not.toBeTrue();
    });
  });

  it('los_dos_guards_when_se_comparan_no_son_el_mismo', () => {
    expect(informesTicketsGuard).not.toBe(informesEscaladosGuard);
  });
});
