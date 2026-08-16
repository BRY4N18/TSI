/**
 * Acceso a los informes tácticos de Cuentas y Clientes.
 *
 * ⚠️ **Son dos guards, no uno.** El backend declara **Administrador** en siete
 * listados y **Administrador o Director Tecnológico** en `accesos-tecnicos`. Un
 * guard único con la unión de roles le daría al Director Tecnológico los siete
 * — que es justo la contradicción con el §5.1 del SRS que `acceso-tactico.md`
 * §5 marca con ⚠️.
 *
 * Y en los dos casos vale la misma regla: **el guard abre la puerta, no decide
 * qué filas se ven**. El alcance lo decide el backend.
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../auth/services/auth-api.service';

/** Los siete listados de cuentas, usuarios y sesiones. */
const ROLES_CUENTAS = ['Administrador'];

/** L8 — accesos técnicos. Suma la única autoridad que el §5.1 reconoce aquí. */
const ROLES_ACCESOS_TECNICOS = ['Administrador', 'DirectorTecnologico'];

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

export const informesCuentasGuard: CanActivateFn = guardDeRoles(ROLES_CUENTAS);

export const informesAccesosTecnicosGuard: CanActivateFn =
  guardDeRoles(ROLES_ACCESOS_TECNICOS);

/** Expuestos para que la prueba compare contra el permiso del backend. */
export const ROLES_INFORMES_CUENTAS = ROLES_CUENTAS;
export const ROLES_INFORMES_ACCESOS_TECNICOS = ROLES_ACCESOS_TECNICOS;
