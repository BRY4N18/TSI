/**
 * Acceso a las pantallas Z de OE6.
 *
 * Un solo guard: §4.6 da los doce informes a Operaciones y Gerente.
 * No es una unión de materias distintas (eso está prohibido en OE1/OE5).
 */
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

export const ROLES_OE6 = ['DirectorOperaciones', 'Gerente'] as const;

export const oe6Guard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);
  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }
  if (!ROLES_OE6.some((rol) => authApi.hasRole(rol))) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }
  return true;
};
