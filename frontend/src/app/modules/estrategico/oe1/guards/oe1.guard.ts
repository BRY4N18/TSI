/**
 * Acceso a las pantallas Z de OE1.
 *
 * Cuatro guards, nunca una unión: el Financiero no debe ver churn;
 * Marketing no debe ver MRR. El Administrador y el Partner no están en §4.1.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

export const ROLES_INGRESO = ['DirectorFinanciero', 'Gerente'] as const;
export const ROLES_CARTERA = ['DirectorEstrategia', 'Gerente'] as const;
export const ROLES_CAPTACION = ['DirectorMarketing', 'Gerente'] as const;
export const ROLES_CICLO = ['Gerente'] as const;

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

export const oe1IngresoGuard: CanActivateFn = guardDe(ROLES_INGRESO);
export const oe1CarteraGuard: CanActivateFn = guardDe(ROLES_CARTERA);
export const oe1CaptacionGuard: CanActivateFn = guardDe(ROLES_CAPTACION);
export const oe1CicloGuard: CanActivateFn = guardDe(ROLES_CICLO);
