/**
 * Acceso a las pantallas Z de OE5.
 *
 * Cuatro guards, nunca una unión: el Financiero no debe ver riesgo;
 * Éxito de Cliente no debe ver NRR. El Administrador y el Partner no están en §4.5.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

export const ROLES_SERVICIO = ['GerenteExitoCliente', 'Gerente'] as const;
export const ROLES_INGRESOS = ['DirectorFinanciero', 'Gerente'] as const;
export const ROLES_PLANES = ['DirectorEstrategia', 'Gerente'] as const;
export const ROLES_RIESGO = ['Gerente'] as const;

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

export const oe5ServicioGuard: CanActivateFn = guardDe(ROLES_SERVICIO);
export const oe5IngresosGuard: CanActivateFn = guardDe(ROLES_INGRESOS);
export const oe5PlanesGuard: CanActivateFn = guardDe(ROLES_PLANES);
export const oe5RiesgoGuard: CanActivateFn = guardDe(ROLES_RIESGO);
