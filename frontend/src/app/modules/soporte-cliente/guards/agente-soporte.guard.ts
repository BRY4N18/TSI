import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

/**
 * ⚠️ Sin `Administrador`: la gestión de tickets es del equipo de soporte.
 *
 * El guard lo admitía y por eso la cola y el detalle de tickets —notas internas
 * incluidas— le aparecían a quien administra la plataforma (hallazgo #18 de la
 * revisión del 24/08/2026). El espejo backend está en
 * `apps/soporte_cliente/permissions.py` (`ROLES_AGENTE`); si cambia uno, cambia
 * el otro.
 */
const ROLES = ['Soporte', 'DesarrolladorAPIs', 'DirectorTecnologico'];

export const agenteSoporteGuard: CanActivateFn = () => {
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
