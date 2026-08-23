/**
 * Acceso a las pantallas Z de gestión de Soporte al Cliente.
 *
 * El guard de listados admite Cliente; el de cola/dashboard no incluye al
 * Gerente e incluye DesarrolladorAPIs / DirectorTecnologico. Reusar cualquiera
 * abriría un enlace que «entra y falla» o dejaría al Gerente sin menú.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

// ⚠️ El `Administrador` **no** está aquí: desde el 2026-08-19 opera el sistema y
// no lee informes de gestión. El backend ya se lo deniega; dejarlo en el guard
// haría que el menú y la ruta le prometieran una pantalla que termina en «Acceso
// denegado», que es peor que no ofrecerla.
export const ROLES_GESTION_SOPORTE = [
  'GerenteExitoCliente',
  'Soporte',
] as const;

export const soporteGestionGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);
  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }
  if (!ROLES_GESTION_SOPORTE.some((rol) => authApi.hasRole(rol))) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }
  return true;
};
