/** @marker unit */
import { TestBed } from '@angular/core/testing';
import { Router, UrlTree, provideRouter } from '@angular/router';

import {
  ROLES_INFORMES_ACCESOS_TECNICOS,
  ROLES_INFORMES_CUENTAS,
  informesAccesosTecnicosGuard,
  informesCuentasGuard,
} from './informes-cuentas.guard';
import { AuthApiService } from '../../auth/services/auth-api.service';

function authStub(roles: string[], autenticado = true) {
  return {
    isAuthenticated: () => autenticado,
    hasRole: (rol: string) => roles.includes(rol),
  };
}

function ejecutar(guard: typeof informesCuentasGuard, roles: string[], autenticado = true) {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [provideRouter([]), { provide: AuthApiService, useValue: authStub(roles, autenticado) }],
  });
  return TestBed.runInInjectionContext(() =>
    guard({} as never, {} as never),
  ) as boolean | UrlTree;
}

describe('Guards de informes de Cuentas y Clientes', () => {
  it('roles_when_se_declaran_coinciden_con_el_permiso_del_backend', () => {
    // `InformesCuentasLecturaPermission` y `InformesAccesosTecnicosPermission`.
    expect(ROLES_INFORMES_CUENTAS).toEqual(['Administrador']);
    expect(ROLES_INFORMES_ACCESOS_TECNICOS).toEqual(['Administrador', 'DirectorTecnologico']);
  });

  describe('los siete listados de cuentas', () => {
    it('administrador_when_entra_pasa', () => {
      expect(ejecutar(informesCuentasGuard, ['Administrador'])).toBeTrue();
    });

    it('director_tecnologico_when_entra_NO_pasa', () => {
      // ⚠️ Es la razón de que haya dos guards. Un guard único con la unión de
      // roles le daría los siete, que es la contradicción con el §5.1 del SRS
      // que `acceso-tactico.md` §5 marca con ⚠️.
      const resultado = ejecutar(informesCuentasGuard, ['DirectorTecnologico']);

      expect(resultado).not.toBeTrue();
      expect(resultado instanceof UrlTree).toBeTrue();
    });

    it('rol_ajeno_when_entra_es_redirigido_y_no_ve_una_tabla_vacia', () => {
      const resultado = ejecutar(informesCuentasGuard, ['Operador']);

      expect(resultado instanceof UrlTree).toBeTrue();
      expect(String(resultado)).toContain('access-denied');
    });

    it('sin_autenticar_when_entra_va_al_login', () => {
      const resultado = ejecutar(informesCuentasGuard, [], false);

      expect(String(resultado)).toContain('login');
    });
  });

  describe('accesos tecnicos', () => {
    it('director_tecnologico_when_entra_aqui_si_pasa', () => {
      expect(ejecutar(informesAccesosTecnicosGuard, ['DirectorTecnologico'])).toBeTrue();
    });

    it('administrador_when_entra_aqui_tambien_pasa', () => {
      expect(ejecutar(informesAccesosTecnicosGuard, ['Administrador'])).toBeTrue();
    });

    it('rol_ajeno_when_entra_no_pasa', () => {
      expect(ejecutar(informesAccesosTecnicosGuard, ['Cliente'])).not.toBeTrue();
    });
  });

  it('los_dos_guards_when_se_comparan_no_son_el_mismo', () => {
    // Si alguien los unificara, esta prueba y la de arriba caerían juntas.
    expect(informesCuentasGuard).not.toBe(informesAccesosTecnicosGuard);
  });
});
