/**
 * Acceso a los informes tácticos de Ventas y CRM.
 *
 * ⚠️ **`reasignaciones` es supervisión pura.** El reparto de cartera es decisión
 * de jefatura, no herramienta del gerente cuya cartera se reparte: solo lo ven
 * los roles amplios. Un guard único se lo daría también a los gerentes.
 *
 * Y como siempre: **el guard abre la puerta, no decide qué filas se ven.** Un
 * gerente entra a los otros tres y el backend lo acota a su propia cartera.
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { INFORME_REASIGNACIONES } from '../definiciones/informes-ventas.definiciones';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

/** Ven toda la cartera. `DirectorMarketing` es la autoridad del departamento. */
const ROLES_AMPLIOS = ['Administrador', 'DirectorMarketing'];

/** Forzados a su propia cartera por el backend. */
const ROLES_ACOTADOS = ['GerenteVentas', 'GerenteCuentasPublicas'];

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

export const informesVentasGuard: CanActivateFn = guardDeRoles([
  ...ROLES_AMPLIOS,
  ...ROLES_ACOTADOS,
]);

export const informesReasignacionesGuard: CanActivateFn = guardDeRoles(ROLES_AMPLIOS);

/** Qué listados ofrece el índice según el rol de quien mira. */
export function listadosVisiblesPara(tieneRol: (rol: string) => boolean): string[] {
  const esAmplio = ROLES_AMPLIOS.some(tieneRol);
  const todos = ['prospectos', 'reasignaciones', 'demos-activas', 'notificaciones-enviadas'];
  return esAmplio ? todos : todos.filter((id) => id !== INFORME_REASIGNACIONES);
}

export const ROLES_INFORMES_AMPLIOS = ROLES_AMPLIOS;
export const ROLES_INFORMES_ACOTADOS = ROLES_ACOTADOS;
