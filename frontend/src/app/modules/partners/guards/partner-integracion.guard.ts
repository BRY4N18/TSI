import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

/**
 * Portal del partner (rol `PartnerIntegracion`, idrol 15).
 *
 * Consola y portal son departamentos distintos: sus sidebars no se fusionan y
 * el partner nunca alcanza `/partners/consola` (design-system § 5, FR-UI-033).
 */
export const ROL_PARTNER_INTEGRACION = 'PartnerIntegracion';

export const partnerIntegracionGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);

  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }

  if (!authApi.hasRole(ROL_PARTNER_INTEGRACION)) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }

  return true;
};
