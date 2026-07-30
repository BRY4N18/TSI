import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

/** Empty `/suscripciones` → home por rol (evita Admin en mi-suscripcion). */
export const suscripcionesHomeRedirect: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);
  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }
  if (authApi.hasRole('DirectorEstrategia')) {
    return router.createUrlTree(['/suscripciones/catalogo-planes']);
  }
  if (authApi.hasRole('Administrador')) {
    return router.createUrlTree(['/suscripciones/aprobaciones-downgrade']);
  }
  if (authApi.hasRole('Cliente') || authApi.hasRole('Proveedor')) {
    return router.createUrlTree(['/suscripciones/mi-suscripcion']);
  }
  return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
};
