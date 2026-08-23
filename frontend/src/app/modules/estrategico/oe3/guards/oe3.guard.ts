/**
 * Acceso a las pantallas Z de OE3.
 *
 * Cuatro guards, nunca una unión: Expansión no ve latencia;
 * Operaciones no ve respaldo. Tecnológico no entra: el GET de E3-02 no lo admite.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

export const ROLES_LATENCIA = ['DirectorOperaciones', 'Gerente'] as const;
export const ROLES_CALIDAD = ['DirectorOperaciones', 'Gerente'] as const;
export const ROLES_CAPACIDAD = ['DirectorExpansion', 'DirectorOperaciones', 'Gerente'] as const;
export const ROLES_RESPALDO = ['DirectorExpansion', 'Gerente'] as const;

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

export const oe3LatenciaGuard: CanActivateFn = guardDe(ROLES_LATENCIA);
export const oe3CalidadGuard: CanActivateFn = guardDe(ROLES_CALIDAD);
export const oe3CapacidadGuard: CanActivateFn = guardDe(ROLES_CAPACIDAD);
export const oe3RespaldoGuard: CanActivateFn = guardDe(ROLES_RESPALDO);
