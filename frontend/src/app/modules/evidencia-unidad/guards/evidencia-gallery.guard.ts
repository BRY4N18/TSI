import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

const GALLERY_ROLES = ['Tecnico', 'Operador', 'Unidad', 'Administrador'];

export const evidenciaGalleryGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);

  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }

  if (!authApi.hasAnyRole(GALLERY_ROLES)) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }

  return true;
};
