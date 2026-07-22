import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

export const directorTecnologicoGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);
  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }
  if (!authApi.hasRole('DirectorTecnologico')) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }
  return true;
};

/** Ejecutar CU-O55 admite ambos roles (RF-REGON-001.5): el Administrador
 * ejecuta el protocolo; el Director Tecnológico queda registrado como
 * aprobador. Ambos deben poder acceder a la página de validación. */
export const administradorODirectorTecnologicoGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);
  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }
  if (!authApi.hasAnyRole(['Administrador', 'DirectorTecnologico'])) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }
  return true;
};
