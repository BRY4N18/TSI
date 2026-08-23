/**
 * Acceso a las pantallas Z de gestión. El guard de workpanels admite Operador
 * y deja fuera al Director: no sirve aquí.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

// ⚠️ El `Administrador` **no** está aquí: desde el 2026-08-19 opera el sistema y
// no lee informes de gestión. El backend ya se lo deniega; dejarlo en el guard
// haría que el menú y la ruta le prometieran una pantalla que termina en «Acceso
// denegado», que es peor que no ofrecerla.
export const ROLES_GESTION_EMERGENCIAS = ['DirectorOperaciones'] as const;

export const emergenciasGestionGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);
  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }
  if (!ROLES_GESTION_EMERGENCIAS.some((rol) => authApi.hasRole(rol))) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }
  return true;
};
