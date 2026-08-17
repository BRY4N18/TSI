/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { UrlTree, provideRouter } from '@angular/router';

import {
  ROLES_INFORMES_ACCESO,
  ROLES_INFORMES_CONTRATO,
  informesAccesoGuard,
  informesContratoGuard,
} from './informes-partners.guard';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

function ejecutar(
  guard: typeof informesAccesoGuard,
  roles: string[],
  autenticado = true,
) {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      {
        provide: AuthApiService,
        useValue: {
          isAuthenticated: () => autenticado,
          hasRole: (r: string) => roles.includes(r),
        },
      },
    ],
  });
  return TestBed.runInInjectionContext(() => guard({} as never, {} as never)) as
    | boolean
    | UrlTree;
}

describe('Guards de informes de Partners y API', () => {
  it('roles_when_se_declaran_coinciden_con_el_permiso_del_backend', () => {
    expect(ROLES_INFORMES_CONTRATO.sort()).toEqual(
      ['Administrador', 'DesarrolladorAPIs', 'DirectorTecnologico'].sort(),
    );
    expect(ROLES_INFORMES_ACCESO.sort()).toEqual(
      ['Administrador', 'DesarrolladorAPIs', 'DirectorTecnologico', 'PartnerIntegracion'].sort(),
    );
  });

  it('los_dos_guards_when_se_comparan_no_son_el_mismo', () => {
    expect(informesAccesoGuard).not.toBe(informesContratoGuard);
  });

  describe('la asimetria del departamento', () => {
    it('partner_when_entra_a_acceso_pasa_y_a_contrato_NO', () => {
      expect(ejecutar(informesAccesoGuard, ['PartnerIntegracion'])).toBeTrue();
      expect(ejecutar(informesContratoGuard, ['PartnerIntegracion'])).not.toBeTrue();
    });

    it('director_tecnologico_when_entra_pasa_a_los_dos', () => {
      expect(ejecutar(informesAccesoGuard, ['DirectorTecnologico'])).toBeTrue();
      expect(ejecutar(informesContratoGuard, ['DirectorTecnologico'])).toBeTrue();
    });

    it('desarrollador_apis_when_entra_pasa_a_los_dos', () => {
      expect(ejecutar(informesAccesoGuard, ['DesarrolladorAPIs'])).toBeTrue();
      expect(ejecutar(informesContratoGuard, ['DesarrolladorAPIs'])).toBeTrue();
    });

    it('administrador_when_entra_pasa_a_los_dos', () => {
      expect(ejecutar(informesAccesoGuard, ['Administrador'])).toBeTrue();
      expect(ejecutar(informesContratoGuard, ['Administrador'])).toBeTrue();
    });

    it('operador_when_entra_no_pasa_a_ninguno', () => {
      expect(ejecutar(informesAccesoGuard, ['OperadorDespacho'])).not.toBeTrue();
      expect(ejecutar(informesContratoGuard, ['OperadorDespacho'])).not.toBeTrue();
    });
  });
});
