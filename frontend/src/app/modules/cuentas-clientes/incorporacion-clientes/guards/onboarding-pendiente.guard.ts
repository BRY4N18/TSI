import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map } from 'rxjs/operators';

import { AuthApiService } from '../../auth/services/auth-api.service';
import { IncorporacionClienteApiService } from '../services/incorporacion-cliente-api.service';

export const onboardingPendienteGuard: CanActivateFn = (route) => {
  const auth = inject(AuthApiService);
  const api = inject(IncorporacionClienteApiService);
  const router = inject(Router);
  const idcliente = Number(route.paramMap.get('idcliente'));

  if (!auth.getProfile()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }

  return api.getOnboardingProgreso(idcliente).pipe(
    map((res) => {
      if (res.data.estado_onboarding === 'Completado') {
        return router.createUrlTree([
          '/cuentas-clientes/gestion-cuenta',
          idcliente,
          'perfil',
        ]);
      }
      return true;
    }),
  );
};
