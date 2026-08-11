import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthApiService } from '../../cuentas-clientes/auth/services/auth-api.service';

/**
 * Solo Administrador — **ni siquiera el Desarrollador de APIs**.
 *
 * `gestorPartnersGuard` no sirve aquí porque admite también a DevAPIs, y la
 * cola de excepciones de facturación no es una vista de plataforma: decidir qué
 * hacer con un excedente que no se pudo cobrar es una decisión de negocio.
 *
 * Es el mismo reparto que aplica el backend: `ExcepcionesFacturacionView` deja
 * entrar a los dos roles para poder consultar, pero la acción de resolver es
 * del Administrador. La UI se queda con el más restrictivo de los dos porque no
 * ofrece consulta pasiva: ofrece una cola de trabajo.
 */
export const ROL_ADMINISTRADOR = 'Administrador';

export const administradorGuard: CanActivateFn = () => {
  const authApi = inject(AuthApiService);
  const router = inject(Router);

  if (!authApi.isAuthenticated()) {
    return router.createUrlTree(['/cuentas-clientes/auth/login']);
  }

  if (!authApi.hasAnyRole([ROL_ADMINISTRADOR])) {
    return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
  }

  return true;
};
