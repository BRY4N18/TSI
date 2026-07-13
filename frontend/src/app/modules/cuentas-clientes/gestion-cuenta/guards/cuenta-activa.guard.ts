import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map } from 'rxjs/operators';

import { CuentaClienteApiService } from '../services/cuenta-cliente-api.service';

export const cuentaActivaGuard: CanActivateFn = (route) => {
  const api = inject(CuentaClienteApiService);
  const router = inject(Router);
  const idcliente = Number(route.paramMap.get('idcliente'));

  return api.getPerfil(idcliente).pipe(
    map((res) => {
      if (res.data.estado === 'Activo') {
        return true;
      }
      return router.createUrlTree(['/cuentas-clientes']);
    }),
  );
};
