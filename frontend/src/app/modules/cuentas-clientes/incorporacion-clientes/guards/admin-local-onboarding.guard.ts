import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map } from 'rxjs/operators';

import { AuthApiService } from '../../auth/services/auth-api.service';
import { IncorporacionClienteApiService } from '../services/incorporacion-cliente-api.service';

export const adminLocalOnboardingGuard: CanActivateFn = (route) => {
  const auth = inject(AuthApiService);
  const api = inject(IncorporacionClienteApiService);
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

  return api.getOnboardingProgreso(idcliente).pipe(
    map(() => true),
  );
};
