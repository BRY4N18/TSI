import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map } from 'rxjs/operators';

import { AuthApiService } from '../../auth/services/auth-api.service';
import { CuentaClienteApiService } from '../services/cuenta-cliente-api.service';

export const adminLocalGuard: CanActivateFn = (route) => {
  const auth = inject(AuthApiService);
  const api = inject(CuentaClienteApiService);
  const router = inject(Router);
  const profile = auth.getProfile();
  const idcliente = Number(route.paramMap.get('idcliente'));

  if (!profile) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }

  return api.getPerfil(idcliente).pipe(
    map((res) => {
      if (res.data.admin_local_id === profile.idusuario) {
        return true;
      }
      return router.createUrlTree(['/cuentas-clientes']);
    }),
  );
};
