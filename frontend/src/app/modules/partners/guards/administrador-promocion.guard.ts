import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

/**
 * RF-PON-008 — la promoción a producción la resuelve **solo un Administrador**.
 *
 * El Desarrollador de APIs gestiona planes y catálogo, pero no firma
 * promociones: si pudiera, la aprobación humana dejaría de ser un control.
 * El backend ya devuelve 403, pero dejar que el usuario llegue al formulario y
 * falle al enviar sería prometer algo que no se puede cumplir (FR-UI-011).
 */
export const ROL_RESUELVE_PROMOCION = 'Administrador';

export const administradorPromocionGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);

  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }

  if (!authApi.hasRole(ROL_RESUELVE_PROMOCION)) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }

  return true;
};
