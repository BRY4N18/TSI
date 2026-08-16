/**
 * Acceso a los informes tácticos de Suscripciones y Facturación.
 *
 * ⚠️ **Dos autoridades distintas, no una.** El catálogo y los precios son
 * materia de **Estrategia**; el resultado económico, de **Finanzas**. Un guard
 * único con la unión daría a cada director el área del otro.
 *
 * | Listado | Autoridad además del Administrador |
 * |---|---|
 * | Suscripciones, solicitudes de cambio | `DirectorEstrategia` |
 * | Facturas, métodos de pago | `DirectorFinanciero` |
 *
 * Los roles de cuenta —Cliente y Proveedor— entran a los cuatro y el backend los
 * acota a la suya. **El guard no decide eso**: un cliente necesita ver su propia
 * deuda, y ahí es donde más importa que la vea.
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { INFORMES_FINANZAS } from '../definiciones/informes-suscripciones.definiciones';
import { AuthApiService } from '../../../cuentas-clientes/auth/services/auth-api.service';

const ROLES_ACOTADOS = ['Cliente', 'Proveedor'];
const AMPLIOS_CATALOGO = ['Administrador', 'DirectorEstrategia'];
const AMPLIOS_FINANZAS = ['Administrador', 'DirectorFinanciero'];

function guardDeRoles(roles: string[]): CanActivateFn {
  return () => {
    const authApi = inject(AuthApiService);
    const router = inject(Router);

    if (!authApi.isAuthenticated()) {
      return router.createUrlTree(['/cuentas-clientes/auth/login']);
    }
    if (!roles.some((rol) => authApi.hasRole(rol))) {
      return router.createUrlTree(['/cuentas-clientes/auth/access-denied']);
    }
    return true;
  };
}

export const informesCatalogoGuard: CanActivateFn = guardDeRoles([
  ...AMPLIOS_CATALOGO,
  ...ROLES_ACOTADOS,
]);

export const informesFinanzasGuard: CanActivateFn = guardDeRoles([
  ...AMPLIOS_FINANZAS,
  ...ROLES_ACOTADOS,
]);

export function listadosVisiblesPara(tieneRol: (rol: string) => boolean): string[] {
  const catalogo = [...AMPLIOS_CATALOGO, ...ROLES_ACOTADOS].some(tieneRol);
  const finanzas = [...AMPLIOS_FINANZAS, ...ROLES_ACOTADOS].some(tieneRol);
  const todos = ['suscripciones', 'facturas', 'solicitudes-cambio-plan', 'metodos-pago'];

  return todos.filter((id) =>
    INFORMES_FINANZAS.includes(id) ? finanzas : catalogo,
  );
}

export const ROLES_AMPLIOS_CATALOGO = AMPLIOS_CATALOGO;
export const ROLES_AMPLIOS_FINANZAS = AMPLIOS_FINANZAS;
export const ROLES_INFORMES_ACOTADOS = ROLES_ACOTADOS;
