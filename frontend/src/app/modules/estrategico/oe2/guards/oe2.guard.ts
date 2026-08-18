/**
 * Acceso a las pantallas Z de OE2.
 *
 * Dos guards, nunca una unión: el Financiero no debe ver latencia de todos.
 * El Administrador y el Partner no están en §4.2.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

export const ROLES_USO_ECOSISTEMA = ['DirectorTecnologico', 'Gerente'] as const;
export const ROLES_DINERO = ['DirectorTecnologico', 'Gerente', 'DirectorFinanciero'] as const;

function guardDe(roles: readonly string[]): CanActivateFn {
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

export const oe2UsoEcosistemaGuard: CanActivateFn = guardDe(ROLES_USO_ECOSISTEMA);
export const oe2DineroGuard: CanActivateFn = guardDe(ROLES_DINERO);
