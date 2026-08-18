/**
 * Acceso a las pantallas Z de gestión de Partners y API.
 *
 * El guard de listados admite PartnerIntegracion y DesarrolladorAPIs.
 * Reusarlo abriría un enlace que «entra y falla» o metería al partner en la
 * comparativa de todos.
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

export const ROLES_GESTION_PARTNERS = ['DirectorTecnologico', 'Administrador'] as const;

export const partnersGestionGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);
  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }
  if (!ROLES_GESTION_PARTNERS.some((rol) => authApi.hasRole(rol))) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }
  return true;
};
