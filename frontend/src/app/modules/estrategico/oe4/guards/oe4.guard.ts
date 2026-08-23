/**
 * Acceso a las pantallas Z de OE4.
 *
 * Cuatro guards, nunca una unión: Operaciones no ve concentración ni cobertura.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

export const ROLES_CALIDAD = ['DirectorDatos', 'DirectorOperaciones', 'Gerente'] as const;
export const ROLES_CONCENTRACION = ['DirectorDatos', 'Gerente'] as const;
export const ROLES_IMPACTO = ['DirectorDatos', 'DirectorOperaciones', 'Gerente'] as const;
export const ROLES_COBERTURA = ['DirectorDatos', 'Gerente'] as const;

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

export const oe4CalidadGuard: CanActivateFn = guardDe(ROLES_CALIDAD);
export const oe4ConcentracionGuard: CanActivateFn = guardDe(ROLES_CONCENTRACION);
export const oe4ImpactoGuard: CanActivateFn = guardDe(ROLES_IMPACTO);
export const oe4CoberturaGuard: CanActivateFn = guardDe(ROLES_COBERTURA);
