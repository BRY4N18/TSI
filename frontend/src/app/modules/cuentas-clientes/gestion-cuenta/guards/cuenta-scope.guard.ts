import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map } from 'rxjs/operators';

import { AuthApiService } from '../../auth/services/auth-api.service';
import { CuentaClienteApiService } from '../services/cuenta-cliente-api.service';

export const cuentaScopeGuard: CanActivateFn = (route) => {
  const auth = inject(AuthApiService);
  const api = inject(CuentaClienteApiService);
  const router = inject(Router);
  const profile = auth.getProfile();
  const idcliente = Number(route.paramMap.get('idcliente'));

  if (!profile) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }

  if (profile.roles.includes('Administrador')) {
    return true;
  }

  if (!profile.roles.includes('Cliente')) {
    return router.createUrlTree(['/cuentas-clientes']);
  }

  return api.getPerfil(idcliente).pipe(
    map(() => true),
    // Errors handled by HTTP interceptor; guard falls through to false on 403
  );
};
