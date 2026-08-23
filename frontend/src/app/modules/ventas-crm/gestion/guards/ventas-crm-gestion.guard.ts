/**
 * Acceso a las pantallas Z de gestión de Ventas y CRM.
 *
 * El guard de listados admite GerenteCuentasPublicas; el backend de compuestos
 * no. Reusarlo abriría un enlace que «entra y falla».
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

// ⚠️ El `Administrador` **no** está aquí: desde el 2026-08-19 opera el sistema y
// no lee informes de gestión. El backend ya se lo deniega; dejarlo en el guard
// haría que el menú y la ruta le prometieran una pantalla que termina en «Acceso
// denegado», que es peor que no ofrecerla.
export const ROLES_GESTION_VENTAS_CRM = [
  'DirectorMarketing',
  'GerenteVentas',
] as const;

export const ventasCrmGestionGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);
  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }
  if (!ROLES_GESTION_VENTAS_CRM.some((rol) => authApi.hasRole(rol))) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }
  return true;
};
