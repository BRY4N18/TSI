/**
 * Acceso a las pantallas Z de gestión de Red Operativa.
 *
 * ⚠️ **Dos guards, nunca una unión.** Un canActivate con Expansión y Tecnológico
 * juntos daría a cada director la materia del otro sin que nada fallara.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

export const ROLES_CRECIMIENTO = ['DirectorExpansion', 'Administrador'] as const;
export const ROLES_VALIDACION = ['DirectorTecnologico', 'Administrador'] as const;

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

export const gestionCrecimientoGuard: CanActivateFn = guardDe(ROLES_CRECIMIENTO);
export const gestionValidacionGuard: CanActivateFn = guardDe(ROLES_VALIDACION);
