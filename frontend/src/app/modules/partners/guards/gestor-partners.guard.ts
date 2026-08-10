import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

/** Quienes gestionan partners: incorporarlos y asignarles su plan de acceso. */
export const ROLES_GESTOR_PARTNERS = ['Administrador', 'DesarrolladorAPIs'];

export const gestorPartnersGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);

  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }

  if (!authApi.hasAnyRole(ROLES_GESTOR_PARTNERS)) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }

  return true;
};
