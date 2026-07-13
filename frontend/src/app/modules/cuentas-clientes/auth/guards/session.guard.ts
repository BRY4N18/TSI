import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../services/auth-api.service';

export const sessionGuard: CanActivateFn = (_route, state) => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);

  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login'], {
      queryParams: { returnUrl: state.url },
    });
  }

  if (authApi.requiresPasswordChange() && !state.url.includes('password-reset')) {
    return router.createUrlTree(['/cuentas-clientes/auth/password-reset'], {
      queryParams: { forced: 'true' },
    });
  }

  return true;
};
