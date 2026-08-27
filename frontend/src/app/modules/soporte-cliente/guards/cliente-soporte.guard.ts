import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

/**
 * "Mis tickets" es la pantalla de **quien reporta**, y eso lo define el backend
 * en `ROLES_REPORTADORES`: Cliente y PartnerIntegracion. Este guard admitía
 * además a Soporte y Administrador, que no tienen tickets propios y por tanto
 * llegaban a una pantalla que el API les respondía 403.
 *
 * `PartnerIntegracion` sí entra: el SRS le reconoce el derecho de disputar su
 * factura, y hasta ahora no tenía por dónde ejercerlo (hallazgo #18).
 */
const ROLES = ['Cliente', 'PartnerIntegracion'];

export const clienteSoporteGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);
  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }
  if (!ROLES.some((role) => authApi.hasRole(role))) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }
  return true;
};
