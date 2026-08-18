/**
 * Acceso a las pantallas Z de gestión de Cuentas y Clientes.
 *
 * ⚠️ **Dos guards, nunca una unión.** Un canActivate con Administrador y
 * Director Tecnológico juntos le daría al Tecnológico el ciclo de vida y la
 * incorporación, que el backend ya niega.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../auth/services/auth-api.service';

export const ROLES_CICLO = ['Administrador'] as const;
export const ROLES_INCORPORACION = ['Administrador'] as const;
export const ROLES_ACCESO = ['DirectorTecnologico', 'Administrador'] as const;

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

export const gestionCicloGuard: CanActivateFn = guardDe(ROLES_CICLO);
export const gestionIncorporacionGuard: CanActivateFn = guardDe(ROLES_INCORPORACION);
export const gestionAccesoGuard: CanActivateFn = guardDe(ROLES_ACCESO);
