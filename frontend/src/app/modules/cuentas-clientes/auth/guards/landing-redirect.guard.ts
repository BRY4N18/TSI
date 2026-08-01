import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { homePathForRoles } from '../services/post-login-home';
import { AuthApiService } from '../services/auth-api.service';

/**
 * Resuelve a dónde va la raíz `/`.
 *
 * Sin sesión: portal comercial público. Con sesión: el home operativo del rol,
 * el mismo que resuelve el login. Antes la raíz redirigía siempre al portal
 * público, así que un usuario ya autenticado que escribía la URL base veía
 * "Iniciar sesión / Registrarme" como si no tuviera sesión.
 */
export const landingRedirectGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);

  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/ventas-crm/planes']);
  }

  if (authApi.requiresPasswordChange()) {
    return router.createUrlTree(['/cuentas-clientes/auth/password-reset'], {
      queryParams: { forced: 'true' },
    });
  }

  return router.createUrlTree([homePathForRoles(authApi.getProfile()?.roles)]);
};
