/**
 * Acceso a los informes tácticos de Partners y API.
 *
 * ⚠️ **Son dos guards, no uno.** El Partner ve tres listados; versiones del
 * contrato y alcance de datos son de gestores y del Director Tecnológico. Un
 * guard único con la unión le daría al Partner los dos de contrato.
 *
 * El guard abre la puerta. El alcance (`acotado_a`) lo decide el backend.
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

/** Lectura de los cinco listados sin acotar (FR-014a). */
export const ROLES_INFORMES_CONTRATO = [
  'Administrador',
  'DesarrolladorAPIs',
  'DirectorTecnologico',
];

/** Los tres de acceso: gestores de informe y el propio partner. */
export const ROLES_INFORMES_ACCESO = [...ROLES_INFORMES_CONTRATO, 'PartnerIntegracion'];

function guardDeRoles(roles: string[]): CanActivateFn {
  return () => {
    const authApi = inject(AuthApiService);
    const router = inject(Router);

    if (!authApi.isAuthenticated()) {
      return router.createUrlTree(['/cuentas-clientes/auth/login']);
    }
    if (!roles.some((rol) => authApi.hasRole(rol))) {
      return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
    }
    return true;
  };
}

export const informesAccesoGuard: CanActivateFn = guardDeRoles(ROLES_INFORMES_ACCESO);
export const informesContratoGuard: CanActivateFn = guardDeRoles(ROLES_INFORMES_CONTRATO);
