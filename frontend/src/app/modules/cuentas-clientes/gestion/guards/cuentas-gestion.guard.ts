/**
 * Acceso a las pantallas Z de gestión de Cuentas y Clientes.
 *
 * ⚠️ **Dos guards, nunca una unión.** Un canActivate con las dos autoridades
 * juntas le daría a cada una la materia de la otra, que el backend ya niega.
 *
 * La autoridad de este departamento está repartida desde el 2026-08-19: el
 * **Director de Cuentas** responde del ciclo de vida y de la incorporación, y el
 * **Director Tecnológico**, solo de los accesos técnicos.
 *
 * ⚠️ El `Administrador` ya no está en ninguno de los tres. Era la única forma de
 * abrir siete de estos informes mientras el departamento no tenía autoridad
 * propia; creado el cargo, deja de hacer falta y vuelve a su papel: operar.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../auth/services/auth-api.service';

export const ROLES_CICLO = ['DirectorCuentas'] as const;
export const ROLES_INCORPORACION = ['DirectorCuentas'] as const;
export const ROLES_ACCESO = ['DirectorTecnologico'] as const;

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
